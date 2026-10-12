// Whole-week generation state: config, submit, poll, retry, resume.
// Contract: rest_api_contract.md section 3.5; design: specs/frontend_week_generation/design.md.
// Slot targeting stays server-side (architecture.md section 1.1).

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { usePolling } from './usePolling.js';
import { usePendingGuard } from './pendingGuard.js';
import { AI_POLL_INTERVAL_MS } from './useAiGeneration.js';
import { MESSAGES } from '../messages/index.js';

export const STORAGE_KEY = 'planner.weekGeneration';
const TERMINAL = new Set(['completed', 'partial', 'failed']);
const DEFAULT_MODE = 'mix'; // G-94

const CLOSED = {
  phase: 'closed',
  mode: DEFAULT_MODE,
  overrideDraft: null,
  weekId: null,
  generationId: null,
  targets: null,
  runStatus: null,
  slotStates: [],
  error: null,
  openSeq: 0,
};

// Each access is guarded: storage may be absent or throw (R47).
function readStoredRun() {
  try {
    const raw = globalThis.sessionStorage.getItem(STORAGE_KEY);
    const run = raw ? JSON.parse(raw) : null;
    return run?.generationId && run.weekId && run.targets ? run : null;
  } catch {
    return null;
  }
}

function writeStoredRun(run) {
  try {
    globalThis.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(run));
  } catch {
    // Persistence is best effort; the flow runs without it.
  }
}

function clearStoredRun() {
  try {
    globalThis.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Same as writeStoredRun.
  }
}

export const retryKey = (day, slot) => `retry:${day}-${slot}`;

function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

// A 4xx will not heal by polling again; network and 5xx errors may.
function isFatal(err) {
  return err instanceof ApiError && err.status >= 400 && err.status < 500;
}

function initialState() {
  const stored = readStoredRun();
  if (!stored) return CLOSED;
  return {
    ...CLOSED,
    phase: 'running',
    weekId: stored.weekId,
    generationId: stored.generationId,
    targets: stored.targets,
  };
}

// The idempotent 200 carries the GET body without `targets` (routing.py): list
// the run's own slots as open ones rather than computing anything.
function targetsOf(response) {
  if (response.targets) return response.targets;
  const openSlots = (response.slots ?? []).map(({ day, slot }) => ({ day, slot }));
  return { openSlots, pinnedSlots: [], skippedPins: [] };
}

function bySlot(a, b) {
  return a.day - b.day || a.slot - b.slot;
}

export function useWeekGeneration({
  active = true,
  signedIn = true,
  weekId = null,
  onSettled,
} = {}) {
  const [state, setState] = useState(initialState);
  const [wasSignedIn, setWasSignedIn] = useState(signedIn);
  const { run, pending } = usePendingGuard();
  const runRef = useRef(0);
  const timerRef = useRef(null);
  const settledRef = useRef(onSettled);
  const hadSessionRef = useRef(false);

  useEffect(() => {
    settledRef.current = onSettled;
  });

  // Logging out drops the run in-render, like usePolling's re-enable pattern.
  if (signedIn !== wasSignedIn) {
    setWasSignedIn(signedIn);
    if (!signedIn) setState(CLOSED);
  }

  const isOpen = state.phase !== 'closed';
  const rulesPoll = usePolling('/v1/rules', undefined, { enabled: active && isOpen });
  const rules = useMemo(() => rulesPoll.data?.rules ?? [], [rulesPoll.data]);
  const availableOptions = rulesPoll.data?.availableOptions ?? null;

  const patch = useCallback((change) => setState((current) => ({ ...current, ...change })), []);

  const stopFollow = useCallback(() => {
    runRef.current += 1;
    globalThis.clearTimeout(timerRef.current);
  }, []);

  const applyRun = useCallback(
    (response) => {
      patch({ runStatus: response.status, slotStates: response.slots ?? [] });
    },
    [patch],
  );

  // Polls until terminal. A bumped run id makes late responses inert (R41 of
  // useAiGeneration); `silent404` is the resume case (R48).
  const follow = useCallback(
    async (generationId, { immediate = false, silent404 = false } = {}) => {
      stopFollow();
      const token = runRef.current;
      let first = immediate;
      while (runRef.current === token) {
        if (!first) {
          await new Promise((resolve) => {
            timerRef.current = globalThis.setTimeout(resolve, AI_POLL_INTERVAL_MS);
          });
        }
        first = false;
        if (runRef.current !== token) return;
        try {
          const response = await apiFetch(`/v1/generations/${generationId}`);
          if (runRef.current !== token) return;
          silent404 = false;
          applyRun(response);
          patch({ error: null });
          if (TERMINAL.has(response.status)) {
            clearStoredRun();
            patch({ phase: 'finished' });
            settledRef.current?.();
            return;
          }
        } catch (err) {
          if (runRef.current !== token) return;
          if (silent404 && err instanceof ApiError && err.status === 404) {
            clearStoredRun();
            setState(CLOSED);
            return;
          }
          if (isFatal(err)) {
            clearStoredRun();
            setState((current) => ({ ...current, phase: 'finished', error: toDetail(err) }));
            return;
          }
          patch({ error: toDetail(err) });
        }
      }
    },
    [stopFollow, applyRun, patch],
  );

  // Resume after a reload once the session is known (R45); cleanup on
  // logout or unmount ends any poll. Storage is dropped only on a real logout.
  useEffect(() => {
    if (!signedIn) {
      if (hadSessionRef.current) clearStoredRun();
      hadSessionRef.current = false;
      return undefined;
    }
    hadSessionRef.current = true;
    const stored = readStoredRun();
    if (stored) follow(stored.generationId, { immediate: true, silent404: true });
    return stopFollow;
  }, [signedIn, follow, stopFollow]);

  const open = useCallback(() => {
    if (!weekId) return;
    stopFollow();
    setState((current) => ({
      ...CLOSED,
      phase: 'configuring',
      weekId,
      openSeq: current.openSeq + 1,
    }));
  }, [weekId, stopFollow]);

  const dismiss = useCallback(() => {
    stopFollow();
    clearStoredRun();
    setState(CLOSED); // the unsubmitted draft goes with it (R17)
  }, [stopFollow]);

  const setMode = useCallback((mode) => patch({ mode }), [patch]);

  // Seeded from the shared rules so an untouched group keeps its meaning (the
  // server replaces a group wholesale, serialization.decode_rule_override).
  const startOverride = useCallback(() => {
    setState((current) => ({
      ...current,
      overrideDraft: {
        categoryCounts: rules
          .filter((rule) => rule.type === 'categoryCount')
          .map(({ category, count }) => ({ category, count })),
        disabledDays: rules.filter((rule) => rule.type === 'disabledDay').map((rule) => rule.day),
      },
    }));
  }, [rules]);

  const setCategoryCount = useCallback((category, count) => {
    setState((current) => {
      if (!current.overrideDraft) return current;
      const others = current.overrideDraft.categoryCounts.filter((c) => c.category !== category);
      const categoryCounts = count == null ? others : [...others, { category, count }];
      return { ...current, overrideDraft: { ...current.overrideDraft, categoryCounts } };
    });
  }, []);

  const setDisabledDays = useCallback((days) => {
    setState((current) =>
      current.overrideDraft
        ? { ...current, overrideDraft: { ...current.overrideDraft, disabledDays: days } }
        : current,
    );
  }, []);

  const submit = useCallback(
    () =>
      run('submit', async () => {
        if (state.phase !== 'configuring') return;
        stopFollow();
        const token = runRef.current;
        const { overrideDraft, mode } = state;
        patch({ phase: 'submitting', error: null });
        try {
          const response = await apiFetch('/v1/generations', {
            method: 'POST',
            body: {
              type: 'week',
              weekId: state.weekId,
              mode,
              ...(overrideDraft ? { ruleOverride: overrideDraft } : {}),
            },
          });
          if (runRef.current !== token) return;
          const targets = targetsOf(response);
          const generationId = response.generationId;
          patch({ generationId, targets, phase: 'running' });
          applyRun(response);
          if (TERMINAL.has(response.status)) {
            patch({ phase: 'finished' });
            settledRef.current?.();
            return;
          }
          writeStoredRun({ generationId, weekId: state.weekId, targets });
          follow(generationId);
        } catch (err) {
          if (runRef.current !== token) return;
          patch({ phase: 'configuring', error: toDetail(err) });
        }
      }),
    [run, state, stopFollow, patch, applyRun, follow],
  );

  const retrySlot = useCallback(
    (day, slot) =>
      run(retryKey(day, slot), async () => {
        const { generationId, weekId: runWeekId, targets } = state;
        if (!generationId) return;
        const token = runRef.current;
        try {
          const response = await apiFetch(
            `/v1/generations/${generationId}/slots/${day}/${slot}/retry`,
            { method: 'POST' },
          );
          if (runRef.current !== token) return;
          applyRun(response);
          patch({ phase: 'running', error: null });
          writeStoredRun({ generationId, weekId: runWeekId, targets });
          follow(generationId);
        } catch (err) {
          if (runRef.current !== token) return;
          patch({ error: toDetail(err) });
        }
      }),
    [run, state, applyRun, patch, follow],
  );

  // Rows: every targeted slot with the server fact overlaid (design.md section 3).
  const slots = useMemo(() => {
    if (!state.targets) return [];
    const byKey = new Map(state.slotStates.map((entry) => [`${entry.day}-${entry.slot}`, entry]));
    const open = (state.targets.openSlots ?? []).map(({ day, slot }) => {
      const entry = byKey.get(`${day}-${slot}`);
      if (entry?.status === 'done') return { day, slot, state: 'done' };
      if (entry?.status === 'error') {
        return { day, slot, state: 'error', message: entry.error?.message ?? null };
      }
      return { day, slot, state: 'running' };
    });
    const pinned = (state.targets.pinnedSlots ?? []).map(({ day, slot }) => ({
      day,
      slot,
      state: 'pinned',
    }));
    return [...open, ...pinned].sort(bySlot);
  }, [state.targets, state.slotStates]);

  const progress = useMemo(
    () => ({
      done: slots.filter((row) => row.state === 'done' || row.state === 'error').length,
      total: state.targets?.openSlots?.length ?? 0,
    }),
    [slots, state.targets],
  );

  return {
    phase: state.phase,
    isOpen,
    isBusy: state.phase === 'submitting' || state.phase === 'running',
    runWeekId: state.weekId,
    panelKey: isOpen ? `${state.weekId}:${state.openSeq}` : null,
    mode: state.mode,
    setMode,
    overrideDraft: state.overrideDraft,
    startOverride,
    setCategoryCount,
    setDisabledDays,
    open,
    close: dismiss,
    dismiss,
    submit,
    retrySlot,
    pending,
    targets: state.targets,
    slots,
    progress,
    skippedPins: state.targets?.skippedPins ?? [],
    error: state.error,
    rules,
    rulesLoading: rulesPoll.data === null,
    availableOptions,
  };
}

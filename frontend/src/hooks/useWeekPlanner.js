// Week planner state (T14, design.md section 4.2, section 5): live-weeks
// once, the selected week polled, and the definitive-slot mutations wired
// to usePolling's optimistic applyMutationMarker.

import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { usePolling } from './usePolling.js';
import { useConfirm } from './useConfirm.js';
import { useRecipeDetail, normalizeRecipeDetail } from './useRecipeDetail.js';
import { parseMarker } from '../realtime/etag.js';
import { MESSAGES } from '../messages/index.js';

const WEEK_DAYS = [1, 2, 3, 4, 5, 6, 7];
const WEEK_SLOTS = [1, 2];

function emptySlot(day, slot) {
  return { day, slot, candidates: [], definitiveId: null, isEmpty: true };
}

// Always 7 days x 2 slots (R1) regardless of which entries the API returned
// - the week read already fills every slot (routing.py `_get_week`), this
// is a defensive normalization, not a recompute of week boundaries.
export function buildWeekViewModel(payload) {
  if (!payload) return null;
  const bySlotKey = new Map(
    (payload.slots ?? []).map((entry) => [`${entry.day}-${entry.slot}`, entry]),
  );
  const days = WEEK_DAYS.map((day) => ({
    day,
    slots: WEEK_SLOTS.map((slot) => {
      const entry = bySlotKey.get(`${day}-${slot}`);
      if (!entry) return emptySlot(day, slot);
      return { ...entry, isEmpty: entry.candidates.length === 0 };
    }),
  }));
  return { weekId: payload.weekId, days };
}

function definitiveUrl(weekId, day, slot) {
  return `/v1/weeks/${weekId}/days/${day}/slots/${slot}/definitive`;
}

function candidatesUrl(weekId, day, slot) {
  return `/v1/weeks/${weekId}/days/${day}/slots/${slot}/candidates`;
}

function candidateUrl(weekId, day, slot, candidateId) {
  return `${candidatesUrl(weekId, day, slot)}/${candidateId}`;
}

// Generic apiFetch + ETag-marker capture, shared by the definitive-slot
// mutations and candidate submission below.
async function mutateWithMarker(url, options) {
  let marker = null;
  await apiFetch(url, {
    ...options,
    onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
  });
  return marker;
}

// R15 / design.md section 4.1: surface `error.detail` verbatim, never a
// composed message.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

export function useWeekPlanner({ active = true } = {}) {
  const [liveWeeks, setLiveWeeks] = useState(null);
  const [designation, setDesignation] = useState('current');
  const [authoringTarget, setAuthoringTarget] = useState(null);
  const [editingTarget, setEditingTarget] = useState(null);
  const [detailSource, setDetailSource] = useState(null);
  const [error, setError] = useState(null);
  const confirm = useConfirm();

  // Gated on `active` (issue stuck-loading-after-login): a mount-once read
  // fails SESSION_EXPIRED before login and never re-runs, same pattern
  // useAdminAccounts.js already uses.
  useEffect(() => {
    if (!active) return undefined;
    let cancelled = false;
    apiFetch('/v1/live-weeks').then(
      (result) => {
        if (!cancelled) {
          setLiveWeeks(result);
          setError(null);
        }
      },
      (err) => {
        if (!cancelled) setError(toDetail(err));
      },
    );
    return () => {
      cancelled = true;
    };
  }, [active]);

  const selectedWeek = liveWeeks?.[designation] ?? null;
  const weekUrl = selectedWeek ? `/v1/weeks/${selectedWeek.weekId}` : null;
  // `enabled` combines both gates (findings 1 and 2): only poll when this view
  // is on screen AND the URL is resolved - `usePolling(null)` would otherwise
  // fetch the literal string "null" before live-weeks resolves.
  const weekPoll = usePolling(weekUrl, undefined, { enabled: weekUrl !== null && active });
  const week = useMemo(() => buildWeekViewModel(weekPoll.data), [weekPoll.data]);
  const detail = useRecipeDetail(detailSource);

  const switchWeek = useCallback((nextDesignation) => setDesignation(nextDesignation), []);

  const openCandidateAuthoring = useCallback(
    (day, slot) => setAuthoringTarget({ weekId: selectedWeek?.weekId ?? null, day, slot }),
    [selectedWeek],
  );
  const closeCandidateAuthoring = useCallback(() => setAuthoringTarget(null), []);

  // Issue add-dish-button-inert: the §3.1 discriminated body goes straight
  // through as `input` - useRecipeAuthoring already shapes it (E2).
  const submitCandidate = useCallback(
    async (input) => {
      if (!authoringTarget) return;
      const { weekId, day, slot } = authoringTarget;
      if (!weekId) return;
      try {
        const marker = await mutateWithMarker(candidatesUrl(weekId, day, slot), {
          method: 'POST',
          body: input,
        });
        weekPoll.applyMutationMarker(marker);
        weekPoll.refetchNow(); // issue ui-not-reflecting-mutations; same root cause as E9/E10
        setError(null);
        setAuthoringTarget(null);
      } catch (err) {
        setError(toDetail(err));
      }
    },
    [authoringTarget, weekPoll],
  );

  // Scope extension (E5-E10): a separate target from `authoringTarget`, so
  // the add path's own state and live assertions stay untouched.
  const openCandidateEdit = useCallback(
    (day, slot, candidate) =>
      setEditingTarget({
        weekId: selectedWeek?.weekId ?? null,
        day,
        slot,
        candidateId: candidate.id,
        recipe: candidate.recipe,
      }),
    [selectedWeek],
  );
  const closeCandidateEdit = useCallback(() => setEditingTarget(null), []);

  const submitCandidateEdit = useCallback(
    async (input) => {
      if (!editingTarget) return;
      const { weekId, day, slot, candidateId } = editingTarget;
      if (!weekId) return;
      try {
        const marker = await mutateWithMarker(candidateUrl(weekId, day, slot, candidateId), {
          method: 'PUT',
          body: input,
        });
        weekPoll.applyMutationMarker(marker);
        weekPoll.refetchNow(); // issue ui-not-reflecting-mutations; same root cause as E9/E10
        setError(null);
        setEditingTarget(null);
      } catch (err) {
        setError(toDetail(err));
      }
    },
    [editingTarget, weekPoll],
  );

  const removeCandidate = useCallback(
    (day, slot, candidateId) => {
      const weekId = selectedWeek?.weekId;
      if (!weekId) return;
      confirm.requestConfirm(MESSAGES.CONFIRM_REMOVE_CANDIDATE, async () => {
        // R18 / FR-UX-04
        try {
          const marker = await mutateWithMarker(candidateUrl(weekId, day, slot, candidateId), {
            method: 'DELETE',
          });
          weekPoll.applyMutationMarker(marker);
          weekPoll.refetchNow(); // issue ui-not-reflecting-mutations; same root cause as E9/E10
          setError(null);
        } catch (err) {
          setError(toDetail(err));
        }
      });
    },
    [selectedWeek, weekPoll, confirm],
  );

  const openDetail = useCallback(
    (candidate) => setDetailSource({ recipe: normalizeRecipeDetail(candidate) }),
    [],
  );
  const closeDetail = useCallback(() => setDetailSource(null), []);

  const promoteDefinitive = useCallback(
    (day, slot, candidateId) => {
      const weekId = selectedWeek?.weekId;
      if (!weekId) return;
      const slotState = week?.days.find((d) => d.day === day)?.slots.find((s) => s.slot === slot);
      const doPromote = async () => {
        try {
          const marker = await mutateWithMarker(definitiveUrl(weekId, day, slot), {
            method: 'PUT',
            body: { candidateId },
          });
          weekPoll.applyMutationMarker(marker);
          weekPoll.refetchNow(); // issue ui-not-reflecting-mutations, E9
          setError(null);
        } catch (err) {
          setError(toDetail(err));
        }
      };
      if (slotState?.definitiveId && slotState.definitiveId !== candidateId) {
        confirm.requestConfirm(MESSAGES.CONFIRM_REPLACE_DEFINITIVE, doPromote); // R18
      } else {
        doPromote();
      }
    },
    [selectedWeek, week, weekPoll, confirm],
  );

  const clearDefinitive = useCallback(
    (day, slot) => {
      const weekId = selectedWeek?.weekId;
      if (!weekId) return;
      confirm.requestConfirm(MESSAGES.CONFIRM_CLEAR_DEFINITIVE, async () => {
        // R18
        try {
          const marker = await mutateWithMarker(definitiveUrl(weekId, day, slot), {
            method: 'DELETE',
          });
          weekPoll.applyMutationMarker(marker);
          weekPoll.refetchNow(); // issue ui-not-reflecting-mutations, E10
          setError(null);
        } catch (err) {
          setError(toDetail(err));
        }
      });
    },
    [selectedWeek, weekPoll, confirm],
  );

  return {
    liveWeeks,
    designation,
    week,
    isLoading: liveWeeks === null || week === null, // R20
    connectionLost: weekPoll.connectionLost,
    switchWeek,
    openCandidateAuthoring,
    authoringTarget,
    closeCandidateAuthoring,
    submitCandidate,
    editingTarget,
    openCandidateEdit,
    closeCandidateEdit,
    submitCandidateEdit,
    removeCandidate,
    openDetail,
    detail: detail.recipe,
    isDetailLoading: detail.isLoading,
    detailError: detail.error,
    closeDetail,
    promoteDefinitive,
    clearDefinitive,
    confirm,
    error, // R15 / design.md section 4.1
  };
}

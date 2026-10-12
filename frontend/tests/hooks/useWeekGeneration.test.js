// @vitest-environment jsdom
// Feature 35 (T2-T4): config, submit, poll, retry and resume of a week run.
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch, ApiError } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { AI_POLL_INTERVAL_MS } from '../../src/hooks/useAiGeneration.js';
import { STORAGE_KEY, useWeekGeneration } from '../../src/hooks/useWeekGeneration.js';
import { MESSAGES } from '../../src/messages/index.js';

const RULES = {
  rules: [
    { type: 'categoryCount', category: 'fish', count: 2 },
    { type: 'disabledDay', day: 6 },
    { type: 'pin', day: 1, slot: 1, recipeId: 'r1', recipeName: 'Lentejas' },
  ],
  availableOptions: {
    maxCountByCategory: { fish: 3 },
    daysAvailableForPin: [2],
    daysAvailableToDisable: [2, 3],
  },
};
const TARGETS = {
  openSlots: [
    { day: 1, slot: 1 },
    { day: 1, slot: 2 },
  ],
  pinnedSlots: [{ day: 2, slot: 1, recipeId: 'r1' }],
  skippedPins: [{ day: 3, slot: 2, recipeId: 'r2' }],
};
const ACCEPTED = { generationId: 'g1', status: 'pending', targets: TARGETS };
const STORED = { generationId: 'g1', weekId: '2026-W34', targets: TARGETS };

function runBody(status, slots) {
  return { generationId: 'g1', status, slots };
}
function apiError(status, detail, code = 'X') {
  return new ApiError({ status, code, detail });
}
function mountHook(props = {}) {
  return renderHook((p) => useWeekGeneration(p), {
    initialProps: { weekId: '2026-W34', onSettled: vi.fn(), ...props },
  });
}
async function tick(ms = AI_POLL_INTERVAL_MS) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}
function callsTo(prefix, method) {
  return apiFetch.mock.calls.filter(
    ([url, options]) => url.startsWith(prefix) && (options?.method ?? 'GET') === method,
  );
}

describe('useWeekGeneration', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    window.sessionStorage.clear();
    usePolling.mockReturnValue({ data: RULES });
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  async function submitted(props) {
    apiFetch.mockResolvedValueOnce(ACCEPTED);
    const hook = mountHook(props);
    act(() => hook.result.current.open());
    await act(async () => {
      await hook.result.current.submit();
    });
    return hook;
  }

  describe('configuration', () => {
    it('opens configuring with mix preselected (R3, R10)', () => {
      const { result } = mountHook();
      expect(result.current.phase).toBe('closed');
      act(() => result.current.open());
      expect(result.current.phase).toBe('configuring');
      expect(result.current.mode).toBe('mix');
    });

    it('does not open without a week id', () => {
      const { result } = mountHook({ weekId: null });
      act(() => result.current.open());
      expect(result.current.phase).toBe('closed');
    });

    it('lists the shared rules and reads them only while open (R11)', () => {
      const { result } = mountHook();
      expect(usePolling).toHaveBeenLastCalledWith('/v1/rules', undefined, { enabled: false });
      act(() => result.current.open());
      expect(usePolling).toHaveBeenLastCalledWith('/v1/rules', undefined, { enabled: true });
      expect(result.current.rules).toEqual(RULES.rules);
      expect(result.current.availableOptions).toEqual(RULES.availableOptions);
    });

    it('discards the override draft and the mode on close (R17)', () => {
      const { result } = mountHook();
      act(() => result.current.open());
      act(() => result.current.setMode('ai_only'));
      act(() => result.current.startOverride());
      expect(result.current.overrideDraft).not.toBeNull();
      act(() => result.current.close());
      act(() => result.current.open());
      expect(result.current.overrideDraft).toBeNull();
      expect(result.current.mode).toBe('mix');
    });

    it('seeds the draft from the shared rules and edits it locally (R12, R13)', () => {
      const { result } = mountHook();
      act(() => result.current.open());
      act(() => result.current.startOverride());
      expect(result.current.overrideDraft).toEqual({
        categoryCounts: [{ category: 'fish', count: 2 }],
        disabledDays: [6],
      });
      act(() => result.current.setCategoryCount('meat', 1));
      act(() => result.current.setCategoryCount('fish', null));
      act(() => result.current.setDisabledDays([3, 6]));
      expect(result.current.overrideDraft).toEqual({
        categoryCounts: [{ category: 'meat', count: 1 }],
        disabledDays: [3, 6],
      });
    });
  });

  describe('submit', () => {
    it('posts the week body without attempt or override when untouched (R14, R19, R20)', async () => {
      await submitted();
      expect(apiFetch).toHaveBeenCalledWith('/v1/generations', {
        method: 'POST',
        body: { type: 'week', weekId: '2026-W34', mode: 'mix' },
      });
    });

    it.each(['library_only', 'ai_only', 'mix'])('sends the chosen mode %s', async (mode) => {
      apiFetch.mockResolvedValueOnce(ACCEPTED);
      const { result } = mountHook();
      act(() => result.current.open());
      act(() => result.current.setMode(mode));
      await act(async () => {
        await result.current.submit();
      });
      expect(apiFetch.mock.calls[0][1].body.mode).toBe(mode);
    });

    it('carries ruleOverride when edited and never writes /v1/rules (R15, R16)', async () => {
      apiFetch.mockResolvedValueOnce(ACCEPTED);
      const { result } = mountHook();
      act(() => result.current.open());
      act(() => result.current.startOverride());
      act(() => result.current.setDisabledDays([6, 7]));
      await act(async () => {
        await result.current.submit();
      });
      expect(apiFetch.mock.calls[0][1].body.ruleOverride).toEqual({
        categoryCounts: [{ category: 'fish', count: 2 }],
        disabledDays: [6, 7],
      });
      expect(apiFetch.mock.calls.some(([url]) => url.startsWith('/v1/rules'))).toBe(false);
    });

    it('shows submitting and keeps a double tap to one request (R18, R21)', async () => {
      let release;
      apiFetch.mockReturnValueOnce(new Promise((resolve) => (release = resolve)));
      const { result } = mountHook();
      act(() => result.current.open());
      act(() => {
        result.current.submit();
        result.current.submit();
      });
      expect(result.current.phase).toBe('submitting');
      expect(callsTo('/v1/generations', 'POST')).toHaveLength(1);
      await act(async () => release(ACCEPTED));
      expect(result.current.phase).toBe('running');
    });

    it('keeps the panel open and shows the detail on rejection (R22)', async () => {
      apiFetch.mockRejectedValueOnce(apiError(422, 'Reglas imposibles.', 'UNSATISFIABLE_RULE_SET'));
      const { result } = mountHook();
      act(() => result.current.open());
      act(() => result.current.startOverride());
      await act(async () => {
        await result.current.submit();
      });
      expect(result.current.phase).toBe('configuring');
      expect(result.current.error).toBe('Reglas imposibles.');
      expect(result.current.overrideDraft).not.toBeNull();
    });

    it('falls back to the generic message for a non-API failure', async () => {
      apiFetch.mockRejectedValueOnce(new Error('boom'));
      const { result } = mountHook();
      act(() => result.current.open());
      await act(async () => {
        await result.current.submit();
      });
      expect(result.current.error).toBe(MESSAGES.GENERIC_ERROR);
    });

    it('turns the 202 into rows, skipped pins and a stored run (R25, R28, R31, R44)', async () => {
      const { result } = await submitted();
      expect(result.current.phase).toBe('running');
      expect(result.current.slots).toEqual([
        { day: 1, slot: 1, state: 'running' },
        { day: 1, slot: 2, state: 'running' },
        { day: 2, slot: 1, state: 'pinned' },
      ]);
      expect(result.current.skippedPins).toEqual(TARGETS.skippedPins);
      expect(JSON.parse(window.sessionStorage.getItem(STORAGE_KEY))).toEqual(STORED);
    });

    it('lists the run own slots when the idempotent 200 has no targets', async () => {
      apiFetch.mockResolvedValueOnce(runBody('completed', [{ day: 4, slot: 2, status: 'done' }]));
      const { result } = mountHook();
      act(() => result.current.open());
      await act(async () => {
        await result.current.submit();
      });
      expect(result.current.phase).toBe('finished');
      expect(result.current.slots).toEqual([{ day: 4, slot: 2, state: 'done' }]);
    });
  });

  describe('polling', () => {
    it('polls on the fixed interval and overlays slot status (R23, R26, R29, R34)', async () => {
      const { result } = await submitted();
      apiFetch.mockResolvedValueOnce(
        runBody('running', [
          { day: 1, slot: 1, status: 'done' },
          { day: 1, slot: 2, status: 'error', error: { code: 'invalid_output', message: 'Mal.' } },
        ]),
      );
      expect(callsTo('/v1/generations/g1', 'GET')).toHaveLength(0);
      await tick();
      expect(callsTo('/v1/generations/g1', 'GET')).toHaveLength(1);
      expect(result.current.slots).toEqual([
        { day: 1, slot: 1, state: 'done' },
        { day: 1, slot: 2, state: 'error', message: 'Mal.' },
        { day: 2, slot: 1, state: 'pinned' },
      ]);
      expect(result.current.progress).toEqual({ done: 2, total: 2 });
    });

    it('exposes an errored slot without a message as null for the view (R35)', async () => {
      const { result } = await submitted();
      apiFetch.mockResolvedValueOnce(runBody('running', [{ day: 1, slot: 1, status: 'error' }]));
      await tick();
      expect(result.current.slots[0]).toEqual({ day: 1, slot: 1, state: 'error', message: null });
    });

    it('stops and clears the stored run on a terminal status (R46)', async () => {
      const { result } = await submitted();
      apiFetch.mockResolvedValueOnce(runBody('partial', []));
      await tick();
      expect(result.current.phase).toBe('finished');
      expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull();
      const before = apiFetch.mock.calls.length;
      await tick(AI_POLL_INTERVAL_MS * 3);
      expect(apiFetch.mock.calls.length).toBe(before);
    });

    it.each(['completed', 'partial', 'failed'])(
      'refetches the week once on %s (R30)',
      async (status) => {
        const onSettled = vi.fn();
        await submitted({ onSettled });
        apiFetch.mockResolvedValueOnce(runBody(status, []));
        await tick();
        expect(onSettled).toHaveBeenCalledTimes(1);
      },
    );

    it('stops polling on unmount', async () => {
      const { unmount } = await submitted();
      unmount();
      const before = apiFetch.mock.calls.length;
      await tick(AI_POLL_INTERVAL_MS * 3);
      expect(apiFetch.mock.calls.length).toBe(before);
    });

    it('keeps polling through a week change (R42)', async () => {
      const { result, rerender } = await submitted();
      rerender({ weekId: '2026-W35', onSettled: vi.fn() });
      apiFetch.mockResolvedValueOnce(runBody('running', []));
      await tick();
      expect(callsTo('/v1/generations/g1', 'GET')).toHaveLength(1);
      expect(result.current.runWeekId).toBe('2026-W34');
    });

    it('shows a transient failure and keeps polling (R40)', async () => {
      const { result } = await submitted();
      apiFetch.mockRejectedValueOnce(apiError(503, 'Servicio no disponible.'));
      await tick();
      expect(result.current.error).toBe('Servicio no disponible.');
      expect(result.current.phase).toBe('running');
      apiFetch.mockResolvedValueOnce(runBody('running', []));
      await tick();
      expect(result.current.error).toBeNull();
    });

    it('stops on a client error so the user can close the report', async () => {
      const { result } = await submitted();
      apiFetch.mockRejectedValueOnce(apiError(404, 'No existe.', 'GENERATION_NOT_FOUND'));
      await tick();
      expect(result.current.phase).toBe('finished');
      expect(result.current.error).toBe('No existe.');
      expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull();
    });
  });

  describe('retry and dismiss', () => {
    async function withErrorSlots() {
      const hook = await submitted();
      apiFetch.mockResolvedValueOnce(
        runBody('failed', [
          { day: 1, slot: 1, status: 'error', error: { code: 'x', message: 'Mal.' } },
          { day: 1, slot: 2, status: 'error', error: { code: 'x', message: 'Mal.' } },
        ]),
      );
      await tick();
      return hook;
    }

    it('posts the retry without a body and resumes polling (R37, R38)', async () => {
      const { result } = await withErrorSlots();
      apiFetch.mockResolvedValueOnce(
        runBody('running', [
          { day: 1, slot: 1, status: 'running' },
          { day: 1, slot: 2, status: 'error', error: { code: 'x', message: 'Mal.' } },
        ]),
      );
      await act(async () => {
        await result.current.retrySlot(1, 1);
      });
      expect(apiFetch).toHaveBeenLastCalledWith('/v1/generations/g1/slots/1/1/retry', {
        method: 'POST',
      });
      expect(result.current.phase).toBe('running');
      expect(result.current.slots[0].state).toBe('running');
      expect(window.sessionStorage.getItem(STORAGE_KEY)).not.toBeNull();
      apiFetch.mockResolvedValueOnce(runBody('partial', []));
      await tick();
      expect(result.current.phase).toBe('finished');
    });

    it('disables that slot retry while it is in flight (R39)', async () => {
      const { result } = await withErrorSlots();
      let release;
      apiFetch.mockReturnValueOnce(new Promise((resolve) => (release = resolve)));
      act(() => {
        result.current.retrySlot(1, 2);
      });
      expect(result.current.pending.has('retry:1-2')).toBe(true);
      expect(result.current.pending.has('retry:1-1')).toBe(false);
      await act(async () => release(runBody('running', [])));
      expect(result.current.pending.has('retry:1-2')).toBe(false);
    });

    it('shows the detail of a failed retry (R40)', async () => {
      const { result } = await withErrorSlots();
      apiFetch.mockRejectedValueOnce(
        apiError(409, 'No se puede reintentar.', 'SLOT_NOT_RETRYABLE'),
      );
      await act(async () => {
        await result.current.retrySlot(1, 1);
      });
      expect(result.current.error).toBe('No se puede reintentar.');
      expect(result.current.phase).toBe('finished');
    });

    it('dismiss closes the report (R41)', async () => {
      const { result } = await withErrorSlots();
      act(() => result.current.dismiss());
      expect(result.current.phase).toBe('closed');
      expect(result.current.slots).toEqual([]);
    });
  });

  describe('resume', () => {
    it('resumes a stored run with an immediate GET (R45)', async () => {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(STORED));
      apiFetch.mockResolvedValueOnce(runBody('running', [{ day: 1, slot: 1, status: 'done' }]));
      const { result } = mountHook();
      expect(result.current.phase).toBe('running');
      expect(result.current.runWeekId).toBe('2026-W34');
      await tick(0);
      expect(callsTo('/v1/generations/g1', 'GET')).toHaveLength(1);
      expect(result.current.slots[0].state).toBe('done');
    });

    it('waits for the session before resuming', async () => {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(STORED));
      apiFetch.mockResolvedValue(runBody('running', []));
      const { rerender } = mountHook({ signedIn: false });
      await tick(0);
      expect(apiFetch).not.toHaveBeenCalled();
      expect(window.sessionStorage.getItem(STORAGE_KEY)).not.toBeNull();
      rerender({ weekId: '2026-W34', signedIn: true });
      await tick(0);
      expect(callsTo('/v1/generations/g1', 'GET')).toHaveLength(1);
    });

    it('drops the stored run silently on 404 (R48)', async () => {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(STORED));
      apiFetch.mockRejectedValueOnce(apiError(404, 'No existe.', 'GENERATION_NOT_FOUND'));
      const { result } = mountHook();
      await tick(0);
      expect(result.current.phase).toBe('closed');
      expect(result.current.error).toBeNull();
      expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull();
    });

    it('clears the run and storage on logout', async () => {
      const { result, rerender } = await submitted();
      rerender({ weekId: '2026-W34', signedIn: false });
      expect(result.current.phase).toBe('closed');
      expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull();
    });

    it('runs without persistence when storage throws (R47)', async () => {
      const denied = () => {
        throw new Error('denied');
      };
      vi.spyOn(window.Storage.prototype, 'getItem').mockImplementation(denied);
      vi.spyOn(window.Storage.prototype, 'setItem').mockImplementation(denied);
      vi.spyOn(window.Storage.prototype, 'removeItem').mockImplementation(denied);
      const { result } = await submitted();
      expect(result.current.phase).toBe('running');
      apiFetch.mockResolvedValueOnce(runBody('completed', []));
      await tick();
      expect(result.current.phase).toBe('finished');
    });
  });
});

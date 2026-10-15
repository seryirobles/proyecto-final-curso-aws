// @vitest-environment jsdom
// Feature 35 (T5): the planner owns the generation hook and refetches on settle.
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useWeekPlanner } from '../../src/hooks/useWeekPlanner.js';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};
const TARGETS = { openSlots: [{ day: 1, slot: 1 }], pinnedSlots: [], skippedPins: [] };

describe('useWeekPlanner generation', () => {
  afterEach(() => {
    window.sessionStorage.clear();
    vi.clearAllMocks();
  });

  it('submits the displayed week id from live-weeks and refetches the week when settled (R19, R30)', async () => {
    const refetchNow = vi.fn();
    usePolling.mockReturnValue({ data: null, applyMutationMarker: vi.fn(), refetchNow });
    apiFetch.mockImplementation(async (url) => {
      if (url === '/v1/live-weeks') return LIVE_WEEKS;
      if (url === '/v1/generations')
        return { generationId: 'g1', status: 'pending', targets: TARGETS };
      return {
        generationId: 'g1',
        status: 'completed',
        slots: [{ day: 1, slot: 1, status: 'done' }],
      };
    });
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());

    act(() => result.current.switchWeek('next'));
    act(() => result.current.generation.open());
    await act(async () => {
      await result.current.generation.submit();
    });

    expect(apiFetch).toHaveBeenCalledWith('/v1/generations', {
      method: 'POST',
      body: { type: 'week', weekId: '2026-W35', mode: 'mix' },
    });
    await waitFor(() => expect(refetchNow).toHaveBeenCalled(), { timeout: 4000 });
    // refetchNow fires in the same tick as the phase patch, before the re-render.
    await waitFor(() => expect(result.current.generation.phase).toBe('finished'), {
      timeout: 4000,
    });
    expect(result.current.generation.runWeekId).toBe('2026-W35');
  });

  it('keeps the run when the week or tab changes (R42)', async () => {
    usePolling.mockReturnValue({ data: null, applyMutationMarker: vi.fn(), refetchNow: vi.fn() });
    apiFetch.mockImplementation(async (url) =>
      url === '/v1/live-weeks'
        ? LIVE_WEEKS
        : { generationId: 'g1', status: 'pending', targets: TARGETS },
    );
    const { result, rerender } = renderHook((p) => useWeekPlanner(p), {
      initialProps: { active: true },
    });
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());
    act(() => result.current.generation.open());
    await act(async () => {
      await result.current.generation.submit();
    });
    rerender({ active: false });
    act(() => result.current.switchWeek('next'));
    expect(result.current.generation.isBusy).toBe(true);
    expect(result.current.generation.runWeekId).toBe('2026-W34');
  });
});

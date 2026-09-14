// @vitest-environment jsdom
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch, ApiError } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useWeekPlanner } from '../../src/hooks/useWeekPlanner.js';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function candidate(id) {
  return {
    id,
    author: 'Marta',
    recipe: {
      name: 'Lentejas al curry',
      category: 'legume',
      servings: 4,
      estimatedTime: '45 min',
      ingredients: [],
      tools: [],
      procedure: [],
    },
  };
}

function weekPayload(weekId) {
  return {
    weekId,
    slots: [
      { day: 1, slot: 1, candidates: [], definitiveId: null },
      { day: 1, slot: 2, candidates: [candidate('c1')], definitiveId: 'c1' },
    ],
  };
}

function pollSnapshot(weekId) {
  return {
    data: weekPayload(weekId),
    marker: 1,
    connectionLost: false,
    applyMutationMarker: vi.fn(),
  };
}

describe('useWeekPlanner', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it('fetches live-weeks once and polls the currently selected week (R1, R2)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));

    renderHook(() => useWeekPlanner());

    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith('/v1/live-weeks'));
    await waitFor(() =>
      expect(usePolling).toHaveBeenCalledWith('/v1/weeks/2026-W34', undefined, {
        enabled: true,
      }),
    );
  });

  it('switchWeek requests the other weekId (R2)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).toEqual(LIVE_WEEKS));

    act(() => result.current.switchWeek('next'));

    await waitFor(() =>
      expect(usePolling).toHaveBeenLastCalledWith('/v1/weeks/2026-W35', undefined, {
        enabled: true,
      }),
    );
    expect(result.current.designation).toBe('next');
  });

  it('returns an identically shaped view-model for the current and the next week (R3)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());
    const currentShape = Object.keys(result.current.week).sort();

    usePolling.mockReturnValue(pollSnapshot('2026-W35'));
    act(() => result.current.switchWeek('next'));

    await waitFor(() => expect(result.current.week.weekId).toBe('2026-W35'));
    expect(Object.keys(result.current.week).sort()).toEqual(currentShape);
    expect(result.current.week.days).toHaveLength(7);
    result.current.week.days.forEach((day) => expect(day.slots).toHaveLength(2));
  });

  it('openDetail is called with the clicked candidate and resolves to a normalized recipe (R4, R5 wiring)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());
    const clicked = result.current.week.days[0].slots[1].candidates[0];

    act(() => result.current.openDetail(clicked));

    expect(result.current.detail).toMatchObject({ name: 'Lentejas al curry', author: 'Marta' });
  });

  it('openCandidateAuthoring records the target day/slot/weekId', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());

    act(() => result.current.openCandidateAuthoring(3, 1));

    expect(result.current.authoringTarget).toEqual({ weekId: '2026-W34', day: 3, slot: 1 });
  });

  it('an empty slot flags isEmpty (R19)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());

    expect(result.current.week.days[0].slots[0].isEmpty).toBe(true);
    expect(result.current.week.days[0].slots[1].isEmpty).toBe(false);
  });

  it('clearDefinitive routes through useConfirm before calling apiFetch (R18)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());
    apiFetch.mockClear();

    act(() => result.current.clearDefinitive(1, 2));

    expect(result.current.confirm.pending).not.toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();

    await act(async () => result.current.confirm.confirm());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/weeks/2026-W34/days/1/slots/2/definitive',
      expect.objectContaining({ method: 'DELETE' }),
    );
  });

  it('promoting a different candidate over an existing definitive routes through useConfirm (R18)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());
    apiFetch.mockClear();

    act(() => result.current.promoteDefinitive(1, 2, 'c2'));

    expect(result.current.confirm.pending).not.toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it('promoting a candidate into an empty slot does not require confirmation', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());
    apiFetch.mockClear();

    await act(async () => result.current.promoteDefinitive(1, 1, 'c9'));

    expect(result.current.confirm.pending).toBeNull();
    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/weeks/2026-W34/days/1/slots/1/definitive',
      expect.objectContaining({ method: 'PUT', body: { candidateId: 'c9' } }),
    );
  });

  it('promoteDefinitive applies the mutation marker parsed from the response ETag (design.md 4.2)', async () => {
    apiFetch.mockImplementation((url, options) => {
      if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
      options?.onHeaders?.(new Headers({ ETag: '"20"' }));
      return Promise.resolve(null);
    });
    const snapshot = pollSnapshot('2026-W34');
    usePolling.mockReturnValue(snapshot);
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());

    await act(async () => result.current.promoteDefinitive(1, 1, 'c9'));

    expect(snapshot.applyMutationMarker).toHaveBeenCalledWith(20);
  });

  it('clearDefinitive applies the mutation marker parsed from the response ETag (design.md 4.2)', async () => {
    apiFetch.mockImplementation((url, options) => {
      if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
      options?.onHeaders?.(new Headers({ ETag: '"20"' }));
      return Promise.resolve(null);
    });
    const snapshot = pollSnapshot('2026-W34');
    usePolling.mockReturnValue(snapshot);
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());

    act(() => result.current.clearDefinitive(1, 2));
    await act(async () => result.current.confirm.confirm());

    expect(snapshot.applyMutationMarker).toHaveBeenCalledWith(20);
  });

  it('sets error to the live-weeks load detail, es-ES verbatim, on failure (R15)', async () => {
    apiFetch.mockRejectedValue(
      new ApiError({ status: 500, code: 'UNKNOWN_ERROR', detail: 'Fallo.' }),
    );
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));

    const { result } = renderHook(() => useWeekPlanner());

    await waitFor(() => expect(result.current.error).toBe('Fallo.'));
  });

  it('promoteDefinitive sets error on a rejected mutation (R15)', async () => {
    apiFetch.mockImplementation((url) => {
      if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
      return Promise.reject(new ApiError({ status: 409, code: 'CONFLICT', detail: 'Conflicto.' }));
    });
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());

    await act(async () => result.current.promoteDefinitive(1, 1, 'c9'));

    expect(result.current.error).toBe('Conflicto.');
  });

  it('clearDefinitive sets error on a rejected mutation (R15)', async () => {
    apiFetch.mockImplementation((url) => {
      if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
      return Promise.reject(new ApiError({ status: 409, code: 'CONFLICT', detail: 'Conflicto.' }));
    });
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());

    act(() => result.current.clearDefinitive(1, 2));
    await act(async () => result.current.confirm.confirm());

    expect(result.current.error).toBe('Conflicto.');
  });

  it('active: false reaches usePolling as enabled: false (App shell finding 1)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot('2026-W34'));

    renderHook(() => useWeekPlanner({ active: false }));

    await waitFor(() =>
      expect(usePolling).toHaveBeenLastCalledWith('/v1/weeks/2026-W34', undefined, {
        enabled: false,
      }),
    );
  });

  it('never polls the literal url "null" before live-weeks resolves (finding 2)', () => {
    apiFetch.mockReturnValue(new Promise(() => {})); // never resolves in this test
    usePolling.mockReturnValue({ data: null, connectionLost: false, applyMutationMarker: vi.fn() });

    renderHook(() => useWeekPlanner());

    expect(usePolling).toHaveBeenCalledWith(null, undefined, { enabled: false });
  });
});

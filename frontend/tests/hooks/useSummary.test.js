// @vitest-environment jsdom
// T40 (R5, R19, R21): fetches live-weeks once, polls the current week's
// summary, exposes the shared openDetail opener, empty-week flag.
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch, ApiError } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useSummary } from '../../src/hooks/useSummary.js';

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

function pollSnapshot(meals) {
  return {
    data: { weekId: '2026-W34', meals },
    connectionLost: false,
    applyMutationMarker: vi.fn(),
  };
}

describe('useSummary', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it('fetches live-weeks once and polls the current week summary (R21)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot([]));

    renderHook(() => useSummary());

    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith('/v1/live-weeks'));
    await waitFor(() =>
      expect(usePolling).toHaveBeenCalledWith('/v1/weeks/2026-W34/summary', undefined, {
        enabled: true,
      }),
    );
  });

  it('active: false reaches usePolling as enabled: false (App shell finding 1)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot([]));

    renderHook(() => useSummary({ active: false }));

    await waitFor(() =>
      expect(usePolling).toHaveBeenLastCalledWith('/v1/weeks/2026-W34/summary', undefined, {
        enabled: false,
      }),
    );
  });

  it('never polls the literal url "null" before live-weeks resolves (finding 2)', () => {
    apiFetch.mockReturnValue(new Promise(() => {})); // never resolves in this test
    usePolling.mockReturnValue({ data: null, connectionLost: false, applyMutationMarker: vi.fn() });

    renderHook(() => useSummary());

    expect(usePolling).toHaveBeenCalledWith(null, undefined, { enabled: false });
  });

  it('zero definitives sets the empty-state flag (R19)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot([]));
    const { result } = renderHook(() => useSummary());

    await waitFor(() => expect(result.current.summary).not.toBeNull());
    expect(result.current.summary.isEmpty).toBe(true);
  });

  it('groups a definitive meal under its exact day and slot, not just present somewhere (R5)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    const meal = candidate('c1');
    usePolling.mockReturnValue(pollSnapshot([{ day: 3, slot: 2, candidate: meal }]));
    const { result } = renderHook(() => useSummary());

    await waitFor(() => expect(result.current.summary.isEmpty).toBe(false));
    const day3 = result.current.summary.days.find((d) => d.day === 3);
    expect(day3.slots.find((s) => s.slot === 2).candidate).toEqual(meal);
    expect(day3.slots.find((s) => s.slot === 1).candidate).toBeNull();
    // Membership, not just presence (Shopping list slice M2 lesson): no other
    // day/slot picks up the same meal.
    result.current.summary.days
      .filter((d) => d.day !== 3)
      .forEach((d) => d.slots.forEach((s) => expect(s.candidate).toBeNull()));
  });

  it('openDetail resolves to a normalized recipe via the shared opener (R5)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    usePolling.mockReturnValue(pollSnapshot([]));
    const { result } = renderHook(() => useSummary());
    await waitFor(() => expect(result.current.summary).not.toBeNull());

    act(() => result.current.openDetail(candidate('c1')));

    expect(result.current.detail).toMatchObject({ name: 'Lentejas al curry', author: 'Marta' });
  });

  it('surfaces the live-weeks fetch error detail (R15)', async () => {
    apiFetch.mockRejectedValue(new ApiError({ status: 500, code: 'SERVER_ERROR', detail: 'boom' }));
    usePolling.mockReturnValue({ data: null, connectionLost: false, applyMutationMarker: vi.fn() });
    const { result } = renderHook(() => useSummary());

    await waitFor(() => expect(result.current.error).toBe('boom'));
  });
});

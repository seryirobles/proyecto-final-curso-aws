// @vitest-environment jsdom
//
// Issue 3 (add-dish-button-inert) cross-check: submitCandidate/
// submitCandidateEdit/removeCandidate share issue 10's weekPoll.
// applyMutationMarker path, split out of the fix-round-2 dispatch brief.
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useWeekPlanner } from '../../src/hooks/useWeekPlanner.js';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

const CANDIDATES_URL = '/v1/weeks/2026-W34/days/1/slots/1/candidates';
const CANDIDATE_URL = `${CANDIDATES_URL}/c-1`;

function candidate(id) {
  return { id, name: `Receta ${id}`, author: 'Marta' };
}

// Same shape as useWeekPlanner.mutationVisibility.test.js's fixture, plus the
// candidates sub-resource this file's three regression cases exercise.
function fakeWeekServer(definitiveId, initialCandidates = [candidate('c-1'), candidate('c-2')]) {
  let marker = 41;
  let definitive = definitiveId;
  let candidates = initialCandidates;
  return vi.fn(async (url, options = {}) => {
    const method = options.method ?? 'GET';
    if (url === '/v1/live-weeks') {
      return { status: 200, ok: true, headers: new Headers(), json: async () => LIVE_WEEKS };
    }
    if (url === '/v1/weeks/2026-W34' && method === 'GET') {
      const held = options.headers?.['If-None-Match'];
      if (held === `"${marker}"`) {
        return { status: 304, ok: false, headers: new Headers({ ETag: held }) };
      }
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({
          weekId: '2026-W34',
          slots: [{ day: 1, slot: 1, candidates, definitiveId: definitive }],
        }),
      };
    }
    if (url === CANDIDATES_URL && method === 'POST') {
      const added = candidate('c-3');
      candidates = [...candidates, added];
      marker += 1;
      return {
        status: 201,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ candidate: added }),
      };
    }
    if (url === CANDIDATE_URL && method === 'PUT') {
      candidates = candidates.map((c) => (c.id === 'c-1' ? { ...c, name: 'Receta editada' } : c));
      marker += 1;
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ candidate: candidates.find((c) => c.id === 'c-1') }),
      };
    }
    if (url === CANDIDATE_URL && method === 'DELETE') {
      candidates = candidates.filter((c) => c.id !== 'c-1');
      marker += 1;
      return { status: 204, ok: true, headers: new Headers({ ETag: `"${marker}"` }) };
    }
    throw new Error(`unexpected ${method} ${url}`);
  });
}

function firstSlot(result) {
  return result.current.week.days.find((d) => d.day === 1).slots.find((s) => s.slot === 1);
}

async function settle() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10); // well below one poll interval
  });
}

describe('useWeekPlanner reflects candidate mutations without a reload', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('a submitted candidate appears in the slot without a reload', async () => {
    globalThis.fetch = fakeWeekServer(null);
    const { result } = renderHook(() => useWeekPlanner());
    await settle();
    act(() => result.current.openCandidateAuthoring(1, 1));

    await act(async () =>
      result.current.submitCandidate({ source: 'manual', recipe: { name: 'Receta c-3' } }),
    );
    await settle();

    expect(firstSlot(result).candidates.map((c) => c.id)).toContain('c-3');
  });

  it('an edited candidate shows its new content in the slot without a reload', async () => {
    globalThis.fetch = fakeWeekServer(null);
    const { result } = renderHook(() => useWeekPlanner());
    await settle();
    act(() => result.current.openCandidateEdit(1, 1, candidate('c-1')));

    await act(async () =>
      result.current.submitCandidateEdit({ source: 'manual', recipe: { name: 'Receta editada' } }),
    );
    await settle();

    const edited = firstSlot(result).candidates.find((c) => c.id === 'c-1');
    expect(edited.name).toBe('Receta editada');
  });

  it('a removed candidate disappears from the slot without a reload', async () => {
    globalThis.fetch = fakeWeekServer(null);
    const { result } = renderHook(() => useWeekPlanner());
    await settle();

    act(() => result.current.removeCandidate(1, 1, 'c-1'));
    await act(async () => result.current.confirm.confirm());
    await settle();

    expect(firstSlot(result).candidates.map((c) => c.id)).not.toContain('c-1');
  });
});

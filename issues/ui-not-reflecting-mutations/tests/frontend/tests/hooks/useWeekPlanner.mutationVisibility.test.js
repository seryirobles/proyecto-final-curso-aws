// @vitest-environment jsdom
//
// Issue 10 (E9, E10): definitive-meal mutations must reach the week grid. Real
// usePolling + real engine; only the fetch boundary is faked.
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useWeekPlanner } from '../../src/hooks/useWeekPlanner.js';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

const DEFINITIVE_URL = '/v1/weeks/2026-W34/days/1/slots/1/definitive';

function candidate(id) {
  return { id, name: `Receta ${id}`, author: 'Marta' };
}

// Minimal week server, honouring `If-None-Match` exactly as
// rest_api_contract.md section 6 does; every mutation bumps the marker once.
function fakeWeekServer(definitiveId) {
  let marker = 41;
  let definitive = definitiveId;
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
          slots: [
            {
              day: 1,
              slot: 1,
              candidates: [candidate('c-1'), candidate('c-2')],
              definitiveId: definitive,
            },
          ],
        }),
      };
    }
    if (url === DEFINITIVE_URL && method === 'DELETE') {
      definitive = null;
      marker += 1;
      return { status: 204, ok: true, headers: new Headers({ ETag: `"${marker}"` }) };
    }
    if (url === DEFINITIVE_URL && method === 'PUT') {
      definitive = JSON.parse(options.body).candidateId;
      marker += 1;
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ candidateId: definitive }),
      };
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

describe('useWeekPlanner reflects its own mutations without a reload', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('a confirmed clear empties the definitive of the slot in the grid (E10)', async () => {
    globalThis.fetch = fakeWeekServer('c-1');
    const { result } = renderHook(() => useWeekPlanner());
    await settle();
    expect(firstSlot(result).definitiveId).toBe('c-1');

    act(() => result.current.clearDefinitive(1, 1));
    await act(async () => result.current.confirm.confirm());
    await settle();

    expect(firstSlot(result).definitiveId).toBe(null);
    expect(result.current.error).toBeNull();
  });

  it('promoting a candidate shows it as the definitive of the slot (E9)', async () => {
    globalThis.fetch = fakeWeekServer(null);
    const { result } = renderHook(() => useWeekPlanner());
    await settle();

    await act(async () => result.current.promoteDefinitive(1, 1, 'c-2'));
    await settle();

    expect(firstSlot(result).definitiveId).toBe('c-2');
  });
});

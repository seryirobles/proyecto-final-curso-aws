// @vitest-environment jsdom
//
// App shell fix round 1, finding 1 - PROOF. Real hooks (nothing mocked but
// the fetch boundary), fake timers: only the active view's poll advances;
// the other 4 stay flat. See progress/impl_frontend_spa.md, "App shell".
import { act, render, cleanup } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch } from '../../src/api/client.js';
import { App } from '../../src/components/App.jsx';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function countsByUrl(calls) {
  return calls.reduce((acc, [url]) => {
    acc[url] = (acc[url] ?? 0) + 1;
    return acc;
  }, {});
}

describe('App polling (finding 1 proof)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    globalThis.fetch = vi.fn().mockResolvedValue({
      status: 200,
      headers: new Headers({ ETag: '"1"' }),
      json: async () => ({}),
    });
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('only the default active view (week) keeps polling after 60s; the other 4 stay flat', async () => {
    await act(async () => {
      render(<App />);
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(60_000);
    });

    const counts = countsByUrl(globalThis.fetch.mock.calls);
    expect(counts['/v1/weeks/2026-W34']).toBe(3);
    expect(counts['/v1/library/recipes']).toBeUndefined();
    expect(counts['/v1/rules']).toBeUndefined();
    expect(counts['/v1/shopping-list']).toBeUndefined();
    expect(counts['/v1/weeks/2026-W34/summary']).toBeUndefined();
  });
});

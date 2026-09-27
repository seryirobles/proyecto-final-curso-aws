// @vitest-environment jsdom
// Issue rule-creation-400-invalid-request: a ruleId holds `#`, which a raw URL
// treats as a fragment and fetch never sends; the whole id must reach the path.
import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useRules } from '../../src/hooks/useRules.js';

function mockPolling(rules = []) {
  usePolling.mockImplementation((url) => ({
    data: url === '/v1/rules' ? { rules, availableOptions: null } : { recipes: [] },
    connectionLost: false,
    applyMutationMarker: vi.fn(),
    refetchNow: vi.fn(),
  }));
}

// What the server receives: fetch drops the fragment, the path arrives encoded.
function ruleIdOnTheWire(path) {
  const url = new URL(path, 'http://localhost');
  return { hash: url.hash, ruleId: decodeURIComponent(url.pathname.replace('/v1/rules/', '')) };
}

function sentPath(method) {
  const call = apiFetch.mock.calls.find(([, options]) => options?.method === method);
  return call[0];
}

describe('useRules ruleId on the wire', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('saveCategoryCount sends the full cat#<category> id, no fragment', async () => {
    apiFetch.mockResolvedValue(null);
    mockPolling();
    const { result } = renderHook(() => useRules());
    act(() => result.current.setCategoryCountCategory('meat'));
    act(() => result.current.setCategoryCountCount('3'));

    await act(async () => result.current.saveCategoryCount());

    expect(ruleIdOnTheWire(sentPath('PUT'))).toEqual({ hash: '', ruleId: 'cat#meat' });
  });

  it('savePin sends the full pin#<day>#<slot> id, no fragment', async () => {
    apiFetch.mockResolvedValue(null);
    mockPolling();
    const { result } = renderHook(() => useRules());
    act(() => result.current.setPinDay('3'));
    act(() => result.current.setPinSlot('2'));
    act(() => result.current.selectPinRecipe('r-9'));

    await act(async () => result.current.savePin());

    expect(ruleIdOnTheWire(sentPath('PUT'))).toEqual({ hash: '', ruleId: 'pin#3#2' });
  });

  it('saveDisabledDay sends the full day#<day> id, no fragment', async () => {
    apiFetch.mockResolvedValue(null);
    mockPolling();
    const { result } = renderHook(() => useRules());
    act(() => result.current.setDisabledDayDay('5'));

    await act(async () => result.current.saveDisabledDay());

    expect(ruleIdOnTheWire(sentPath('PUT'))).toEqual({ hash: '', ruleId: 'day#5' });
  });

  it('remove sends the full rule id, no fragment', async () => {
    apiFetch.mockResolvedValue(null);
    const rule = { type: 'categoryCount', category: 'fish', count: 1 };
    mockPolling([rule]);
    const { result } = renderHook(() => useRules());

    act(() => result.current.remove(rule));
    await act(async () => result.current.confirm.confirm());

    expect(ruleIdOnTheWire(sentPath('DELETE'))).toEqual({ hash: '', ruleId: 'cat#fish' });
  });
});

// @vitest-environment jsdom
// T32 (R18, no R<n> for rule semantics - FR-RULE-01...07, features 6/27):
// PUT/DELETE wiring, useConfirm gating, and UNSATISFIABLE_RULE_SET's
// details.conflicts rendering.
import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch, ApiError } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useRules } from '../../src/hooks/useRules.js';

function pollSnapshot(data) {
  return {
    data,
    connectionLost: false,
    applyMutationMarker: vi.fn(),
    refetchNow: vi.fn(), // issue ui-not-reflecting-mutations
  };
}

function mockPolling({ rules = [], recipes = [] } = {}) {
  usePolling.mockImplementation((url) => {
    if (url === '/v1/rules') return pollSnapshot({ rules });
    if (url === '/v1/library/recipes') return pollSnapshot({ recipes });
    return pollSnapshot(null);
  });
}

describe('useRules', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it("groups the polled rules by type, passing a pin's recipeName through unchanged", () => {
    mockPolling({
      rules: [
        { type: 'categoryCount', category: 'meat', count: 2 },
        { type: 'pin', day: 1, slot: 1, recipeId: 'r-1', recipeName: 'Tortilla' },
        { type: 'disabledDay', day: 7 },
      ],
    });
    const { result } = renderHook(() => useRules());

    expect(result.current.categoryCounts).toHaveLength(1);
    expect(result.current.pins).toHaveLength(1);
    expect(result.current.pins[0].recipeName).toBe('Tortilla');
    expect(result.current.disabledDays).toHaveLength(1);
  });

  it('saveCategoryCount PUTs cat#<category> with the chosen count', async () => {
    apiFetch.mockResolvedValue(null);
    mockPolling();
    const { result } = renderHook(() => useRules());
    act(() => result.current.setCategoryCountCategory('meat'));
    act(() => result.current.setCategoryCountCount('3'));

    await act(async () => result.current.saveCategoryCount());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/rules/cat#meat',
      expect.objectContaining({
        method: 'PUT',
        body: { type: 'categoryCount', category: 'meat', count: 3 },
      }),
    );
  });

  it('savePin PUTs pin#<day>#<slot> with the picked recipeId (R12)', async () => {
    apiFetch.mockResolvedValue(null);
    mockPolling();
    const { result } = renderHook(() => useRules());
    act(() => result.current.setPinDay('3'));
    act(() => result.current.setPinSlot('2'));
    act(() => result.current.selectPinRecipe('r-9'));

    await act(async () => result.current.savePin());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/rules/pin#3#2',
      expect.objectContaining({
        method: 'PUT',
        body: { type: 'pin', day: 3, slot: 2, recipeId: 'r-9' },
      }),
    );
  });

  it('saveDisabledDay PUTs day#<day>', async () => {
    apiFetch.mockResolvedValue(null);
    mockPolling();
    const { result } = renderHook(() => useRules());
    act(() => result.current.setDisabledDayDay('5'));

    await act(async () => result.current.saveDisabledDay());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/rules/day#5',
      expect.objectContaining({ method: 'PUT', body: { type: 'disabledDay', day: 5 } }),
    );
  });

  it('remove routes through useConfirm before calling apiFetch (R18)', async () => {
    apiFetch.mockResolvedValue(null);
    mockPolling({ rules: [{ type: 'disabledDay', day: 7 }] });
    const { result } = renderHook(() => useRules());
    const rule = { type: 'disabledDay', day: 7 };

    act(() => result.current.remove(rule));

    expect(result.current.confirm.pending).not.toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();

    await act(async () => result.current.confirm.confirm());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/rules/day#7',
      expect.objectContaining({ method: 'DELETE' }),
    );
  });

  it('an UNSATISFIABLE_RULE_SET ApiError renders details.conflicts as es-ES text', async () => {
    apiFetch.mockRejectedValue(
      new ApiError({
        status: 422,
        code: 'UNSATISFIABLE_RULE_SET',
        detail: 'El conjunto de reglas no es satisfacible.',
        details: { conflicts: [{ type: 'disabledDay', day: 3 }] },
      }),
    );
    mockPolling();
    const { result } = renderHook(() => useRules());
    act(() => result.current.setDisabledDayDay('3'));

    await act(async () => result.current.saveDisabledDay());

    expect(result.current.error).toContain('El conjunto de reglas no es satisfacible.');
    expect(result.current.error).toContain('miércoles');
  });

  it('active: false reaches both its own poll and its picker as enabled: false (App shell finding 1)', () => {
    mockPolling();

    renderHook(() => useRules({ active: false }));

    expect(usePolling).toHaveBeenCalledWith('/v1/rules', undefined, { enabled: false });
    expect(usePolling).toHaveBeenCalledWith('/v1/library/recipes', undefined, {
      enabled: false,
    });
  });

  it('a rejected save with no conflicts falls back to the plain error detail (R15)', async () => {
    apiFetch.mockRejectedValue(
      new ApiError({ status: 422, code: 'INVALID_WEEKDAY', detail: 'Día no válido.' }),
    );
    mockPolling();
    const { result } = renderHook(() => useRules());
    act(() => result.current.setDisabledDayDay('3'));

    await act(async () => result.current.saveDisabledDay());

    expect(result.current.error).toBe('Día no válido.');
  });
});

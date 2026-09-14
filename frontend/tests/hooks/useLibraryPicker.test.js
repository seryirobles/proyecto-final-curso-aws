// @vitest-environment jsdom
// T30 (R11, R13, R14); F1 fix round 1 - the poll targets the fixed
// unfiltered URI regardless of filters (rest_api_contract.md section 7 Q7);
// name/category filter the already-polled list client-side.
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { usePolling } from '../../src/hooks/usePolling.js';
import { useLibraryPicker } from '../../src/hooks/useLibraryPicker.js';

describe('useLibraryPicker', () => {
  it('polls the unfiltered URI, enabled by default', () => {
    usePolling.mockReturnValue({ data: null, connectionLost: false });

    renderHook(() => useLibraryPicker());

    expect(usePolling).toHaveBeenCalledWith('/v1/library/recipes', undefined, { enabled: true });
  });

  it('passes enabled: false through to usePolling (F2)', () => {
    usePolling.mockReturnValue({ data: null, connectionLost: false });

    renderHook(() => useLibraryPicker({ enabled: false }));

    expect(usePolling).toHaveBeenCalledWith('/v1/library/recipes', undefined, { enabled: false });
  });

  it('never re-polls a filtered URL - the same unfiltered URI is used across filter changes (F1)', () => {
    usePolling.mockReturnValue({ data: null, connectionLost: false });
    const { result } = renderHook(() => useLibraryPicker());

    act(() => result.current.setName('lentejas'));
    act(() => result.current.setCategory('legume'));

    for (const call of usePolling.mock.calls) {
      expect(call[0]).toBe('/v1/library/recipes');
    }
  });

  it('the filter state object has exactly the keys name/category, nothing else (R14)', () => {
    usePolling.mockReturnValue({ data: null, connectionLost: false });
    const { result } = renderHook(() => useLibraryPicker());

    expect(Object.keys(result.current.filters).sort()).toEqual(['category', 'name']);
  });

  it('exposes the polled recipes when no filter is set', () => {
    usePolling.mockReturnValue({
      data: { recipes: [{ id: 'r-1', name: 'Lentejas al curry', category: 'legume' }] },
      connectionLost: false,
    });

    const { result } = renderHook(() => useLibraryPicker());

    expect(result.current.recipes).toEqual([
      { id: 'r-1', name: 'Lentejas al curry', category: 'legume' },
    ]);
  });

  it('filters the polled recipes client-side by name (R11)', () => {
    usePolling.mockReturnValue({
      data: {
        recipes: [
          { id: 'r-1', name: 'Lentejas al curry', category: 'legume' },
          { id: 'r-2', name: 'Tortilla', category: 'eggs' },
        ],
      },
      connectionLost: false,
    });
    const { result } = renderHook(() => useLibraryPicker());

    act(() => result.current.setName('lente'));

    expect(result.current.recipes.map((r) => r.id)).toEqual(['r-1']);
  });

  it('filters the polled recipes client-side by category (R13)', () => {
    usePolling.mockReturnValue({
      data: {
        recipes: [
          { id: 'r-1', name: 'Lentejas al curry', category: 'legume' },
          { id: 'r-2', name: 'Tortilla', category: 'eggs' },
        ],
      },
      connectionLost: false,
    });
    const { result } = renderHook(() => useLibraryPicker());

    act(() => result.current.setCategory('eggs'));

    expect(result.current.recipes.map((r) => r.id)).toEqual(['r-2']);
  });
});

// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

// T27 - useRecipeAuthoring now composes useLibraryPicker for two call sites;
// stub the poll so this hook's own tests never issue a real fetch.
vi.mock('../../src/hooks/usePolling.js', () => ({
  usePolling: vi.fn(() => ({ data: null, connectionLost: false })),
}));

import { usePolling } from '../../src/hooks/usePolling.js';
import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';

describe('useRecipeAuthoring', () => {
  it('mode "candidate" exposes exactly the three methods, in order (R6)', () => {
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'candidate', onSubmit: vi.fn() }),
    );

    expect(result.current.methods).toEqual(['library', 'scratch', 'ai']);
  });

  it('mode "library" exposes exactly the two methods, "library" absent (R7, R8)', () => {
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit: vi.fn() }));

    expect(result.current.methods).toEqual(['scratch', 'ai']);
    expect(result.current.methods).not.toContain('library');
  });

  it('submitting the scratch method posts the exact manual body shape (rest_api_contract.md 3.1)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'candidate', onSubmit }));

    act(() => result.current.setMethod('scratch'));
    act(() => result.current.updateField('name', 'Lentejas al curry'));
    act(() => result.current.updateField('category', 'legume'));
    act(() => result.current.updateField('servings', '4'));
    act(() => result.current.updateField('estimatedTime', '45 min'));
    act(() => result.current.addIngredient());
    act(() => result.current.updateIngredient(0, 'name', 'lentejas'));
    act(() => result.current.updateIngredient(0, 'quantity', '300'));
    act(() => result.current.updateIngredient(0, 'unit', 'g'));
    act(() => result.current.addTool());
    act(() => result.current.updateTool(0, 'olla'));
    act(() => result.current.addProcedureStep());
    act(() => result.current.updateProcedureStep(0, 'Sofreír la cebolla.'));

    act(() => result.current.submit());

    expect(onSubmit).toHaveBeenCalledWith({
      source: 'manual',
      recipe: {
        name: 'Lentejas al curry',
        category: 'legume',
        servings: '4',
        estimatedTime: '45 min',
        ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
        tools: ['olla'],
        procedure: ['Sofreír la cebolla.'],
      },
    });
  });

  it('the ai method never submits, even with a reference recipe and notes filled in (F3, design.md 1.3)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'candidate', onSubmit }));

    act(() => result.current.setMethod('ai'));
    act(() => result.current.selectReferenceRecipe('ref-1'));
    act(() => result.current.updateAiSpec('notes', 'Sin gluten'));

    expect(result.current.canSubmit).toBe(false);

    act(() => result.current.submit());

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('exposes independent library and reference pickers (R12, T27)', () => {
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'candidate', onSubmit: vi.fn() }),
    );

    act(() => result.current.selectLibraryRecipe('lib-1'));
    act(() => result.current.selectReferenceRecipe('ref-1'));

    expect(result.current.libraryRecipeId).toBe('lib-1');
    expect(result.current.referenceRecipeId).toBe('ref-1');
    expect(result.current.libraryPicker.filters).toEqual({ name: '', category: '' });
    expect(result.current.referencePicker.filters).toEqual({ name: '', category: '' });
  });

  it('gates each picker poll to its own active tab - never both at once (F2)', () => {
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'candidate', onSubmit: vi.fn() }),
    );

    // Ordered, not sorted (finding 1, fix round 2) - a sorted pair can't tell
    // the two calls apart, so a swap between them still passes.
    const lastTwo = () => usePolling.mock.calls.slice(-2).map((call) => call[2].enabled);
    const [libraryCall, referenceCall] = lastTwo();
    expect([libraryCall, referenceCall]).toEqual([true, false]);

    act(() => result.current.setMethod('ai'));

    const [libraryCallAfter, referenceCallAfter] = lastTwo();
    expect([libraryCallAfter, referenceCallAfter]).toEqual([false, true]);
  });

  it('active: false ANDs with the method gate on both pickers (App shell finding 1)', () => {
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'candidate', onSubmit: vi.fn(), active: false }),
    );
    act(() => result.current.setMethod('library'));

    const lastTwo = () => usePolling.mock.calls.slice(-2).map((call) => call[2].enabled);
    expect(lastTwo()).toEqual([false, false]);
  });

  it('mode "library" never enables the library-method picker - no "library" method exists (F2, R8)', () => {
    renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit: vi.fn() }));

    // libraryPicker is created first, before referencePicker, each render.
    const [libraryPickerCall] = usePolling.mock.calls.slice(-2);
    expect(libraryPickerCall[2].enabled).toBe(false);
  });

  it('seeds the manual form from initialRecipe, and re-seeds when it changes (F4)', () => {
    const recipeA = {
      name: 'Lentejas al curry',
      category: 'legume',
      servings: 2,
      estimatedTime: '45 min',
      ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
      tools: ['olla'],
      procedure: ['Sofreír.'],
    };
    const { result, rerender } = renderHook(
      ({ initialRecipe }) =>
        useRecipeAuthoring({ mode: 'library', onSubmit: vi.fn(), initialRecipe }),
      { initialProps: { initialRecipe: recipeA } },
    );

    expect(result.current.form).toEqual({
      ...recipeA,
      servings: '2',
      ingredients: [{ name: 'lentejas', quantity: '300', unit: 'g' }],
    });

    rerender({ initialRecipe: null });

    expect(result.current.form).toEqual({
      name: '',
      category: '',
      servings: '',
      estimatedTime: '',
      ingredients: [],
      tools: [],
      procedure: [],
    });
  });

  it('the ai method never issues a POST /v1/generations call (design.md 1.3)', () => {
    globalThis.fetch = vi.fn();
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'candidate', onSubmit: vi.fn() }),
    );

    act(() => result.current.setMethod('ai'));
    act(() => result.current.updateAiSpec('ingredients', 'pasta, tomate'));
    act(() => result.current.submit());

    expect(globalThis.fetch).not.toHaveBeenCalled();
  });
});

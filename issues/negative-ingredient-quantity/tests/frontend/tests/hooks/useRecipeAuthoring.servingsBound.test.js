// @vitest-environment jsdom
// Issue 7 (negative-ingredient-quantity), servings extension, E10: the form
// never submits a servings count that is present and not strictly positive.
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/usePolling.js', () => ({
  usePolling: vi.fn(() => ({ data: null, connectionLost: false })),
}));

import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';

function fillScratchForm(result, servings) {
  act(() => result.current.setMethod('scratch'));
  act(() => result.current.updateField('name', 'Lentejas al curry'));
  act(() => result.current.updateField('category', 'legume'));
  act(() => result.current.updateField('servings', servings));
  act(() => result.current.addIngredient());
  act(() => result.current.updateIngredient(0, 'name', 'lentejas'));
  act(() => result.current.updateIngredient(0, 'quantity', '300'));
  act(() => result.current.updateIngredient(0, 'unit', 'g'));
  act(() => result.current.addTool());
  act(() => result.current.updateTool(0, 'olla'));
  act(() => result.current.addProcedureStep());
  act(() => result.current.updateProcedureStep(0, 'Cocer las lentejas.'));
}

describe('useRecipeAuthoring - servings bound', () => {
  it.each(['-4', '-1', '0'])('does not submit the form with servings %s', (servings) => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit }));

    fillScratchForm(result, servings);
    act(() => result.current.submit());

    expect(result.current.canSubmit).toBe(false);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it.each([
    ['4', 4],
    ['', null],
  ])('submits the form with servings "%s" (still optional)', (servings, wire) => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit }));

    fillScratchForm(result, servings);
    act(() => result.current.submit());

    expect(result.current.canSubmit).toBe(true);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        source: 'manual',
        recipe: expect.objectContaining({ servings: wire }),
      }),
    );
  });
});

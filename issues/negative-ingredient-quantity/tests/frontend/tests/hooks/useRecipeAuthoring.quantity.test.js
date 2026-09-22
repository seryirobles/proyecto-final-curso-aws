// @vitest-environment jsdom
// Issue 7 (negative-ingredient-quantity), E4: the authoring form never submits
// an ingredient whose quantity is not strictly positive.
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/usePolling.js', () => ({
  usePolling: vi.fn(() => ({ data: null, connectionLost: false })),
}));

import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';

function fillScratchForm(result, quantity) {
  act(() => result.current.setMethod('scratch'));
  act(() => result.current.updateField('name', 'Lentejas al curry'));
  act(() => result.current.updateField('category', 'legume'));
  act(() => result.current.addIngredient());
  act(() => result.current.updateIngredient(0, 'name', 'lentejas'));
  act(() => result.current.updateIngredient(0, 'quantity', quantity));
  act(() => result.current.updateIngredient(0, 'unit', 'g'));
  act(() => result.current.addTool());
  act(() => result.current.updateTool(0, 'olla'));
  act(() => result.current.addProcedureStep());
  act(() => result.current.updateProcedureStep(0, 'Cocer las lentejas.'));
}

describe('useRecipeAuthoring ingredient quantity', () => {
  it.each(['-300', '-0.5', '0'])('does not submit the form with quantity %s', (quantity) => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit }));

    fillScratchForm(result, quantity);
    act(() => result.current.submit());

    expect(result.current.canSubmit).toBe(false);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits the form with a positive quantity', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit }));

    fillScratchForm(result, '300');
    act(() => result.current.submit());

    expect(result.current.canSubmit).toBe(true);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        source: 'manual',
        recipe: expect.objectContaining({
          ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
        }),
      }),
    );
  });
});

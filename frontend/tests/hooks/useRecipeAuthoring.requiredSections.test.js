// @vitest-environment jsdom
// Issue 8 (recipe-saved-without-required-sections), E6: the authoring form
// never submits a recipe with an empty ingredientes, utensilios or
// elaboración section (G-89, FR-LIB-03).
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/usePolling.js', () => ({
  usePolling: vi.fn(() => ({ data: null, connectionLost: false })),
}));

import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';

function fillScratchForm(result, { ingredients = true, tools = true, procedure = true } = {}) {
  act(() => result.current.setMethod('scratch'));
  act(() => result.current.updateField('name', 'Lentejas al curry'));
  act(() => result.current.updateField('category', 'legume'));
  if (ingredients) {
    act(() => result.current.addIngredient());
    act(() => result.current.updateIngredient(0, 'name', 'lentejas'));
    act(() => result.current.updateIngredient(0, 'quantity', '300'));
    act(() => result.current.updateIngredient(0, 'unit', 'g'));
  }
  if (tools) {
    act(() => result.current.addTool());
    act(() => result.current.updateTool(0, 'olla'));
  }
  if (procedure) {
    act(() => result.current.addProcedureStep());
    act(() => result.current.updateProcedureStep(0, 'Cocer las lentejas.'));
  }
}

describe('useRecipeAuthoring required recipe sections', () => {
  it.each([
    ['ingredients', { ingredients: false }],
    ['tools', { tools: false }],
    ['procedure', { procedure: false }],
  ])('does not submit a recipe with no %s', (_section, missing) => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit }));

    fillScratchForm(result, missing);
    act(() => result.current.submit());

    expect(result.current.canSubmit).toBe(false);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('does not submit a recipe whose three sections are all empty', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit }));

    fillScratchForm(result, { ingredients: false, tools: false, procedure: false });
    act(() => result.current.submit());

    expect(result.current.canSubmit).toBe(false);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits a recipe carrying one item in each section (E7)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit }));

    fillScratchForm(result);
    act(() => result.current.submit());

    expect(result.current.canSubmit).toBe(true);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        source: 'manual',
        recipe: expect.objectContaining({
          ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
          tools: ['olla'],
          procedure: ['Cocer las lentejas.'],
        }),
      }),
    );
  });
});

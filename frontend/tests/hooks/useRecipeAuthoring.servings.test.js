// @vitest-environment jsdom
// Issue 4 (E1, E2): `servings` is a JSON number on the wire
// (rest_api_contract.md 3.1). `estimatedTime`'s own G-85 free-text cases moved
// to useRecipeAuthoring.estimatedTime.test.js - G-90 supersedes that shape for
// this field (issue tiempo-estimado-numeric-minutes).
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/usePolling.js', () => ({
  usePolling: vi.fn(() => ({ data: null, connectionLost: false })),
}));

import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';

// Non-empty sections (issue recipe-saved-without-required-sections, G-89):
// this file is about servings, not section cardinality.
function submitScratch(result, fields) {
  act(() => result.current.setMethod('scratch'));
  act(() => result.current.updateField('name', 'Lentejas al curry'));
  act(() => result.current.updateField('category', 'legume'));
  act(() => result.current.addIngredient());
  act(() => result.current.updateIngredient(0, 'name', 'lentejas'));
  act(() => result.current.updateIngredient(0, 'quantity', '300'));
  act(() => result.current.updateIngredient(0, 'unit', 'g'));
  act(() => result.current.addTool());
  act(() => result.current.updateTool(0, 'olla'));
  act(() => result.current.addProcedureStep());
  act(() => result.current.updateProcedureStep(0, 'Cocer las lentejas.'));
  for (const [field, value] of Object.entries(fields)) {
    act(() => result.current.updateField(field, value));
  }
  act(() => result.current.submit());
}

function submittedRecipe(onSubmit) {
  return onSubmit.mock.calls[0][0].recipe;
}

describe('useRecipeAuthoring - servings and estimated time on the wire', () => {
  it('sends servings as a number, not the raw input string (E1)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'candidate', onSubmit }));

    submitScratch(result, { servings: '4' });

    expect(submittedRecipe(onSubmit).servings).toBe(4);
  });

  it('sends servings as null when the field is left empty (E2)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'candidate', onSubmit }));

    submitScratch(result, { estimatedTime: '45' });

    expect(submittedRecipe(onSubmit).servings).toBeNull();
  });

  it('re-sends an edited recipe servings as a number, not a string (E1, edit path)', () => {
    const onSubmit = vi.fn();
    // Non-empty sections (issue recipe-saved-without-required-sections, G-89).
    const initialRecipe = {
      name: 'Receta r-1',
      category: 'legume',
      servings: 2,
      estimatedTime: '30 min',
      ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
      tools: ['olla'],
      procedure: ['Cocer las lentejas.'],
    };
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'library', onSubmit, initialRecipe }),
    );

    act(() => result.current.setMethod('scratch'));
    act(() => result.current.submit());

    expect(submittedRecipe(onSubmit).servings).toBe(2);
  });
});

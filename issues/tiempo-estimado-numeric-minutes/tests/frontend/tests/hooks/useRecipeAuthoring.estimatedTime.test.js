// @vitest-environment jsdom
// Issue 11 (E2): `estimatedTime` goes on the wire as a JSON number of minutes
// or null (rest_api_contract.md 3.1 as amended by G-90), the same transport
// cast `servings` already gets. Replaces the two G-85 free-text cases in
// useRecipeAuthoring.servings.test.js.
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/usePolling.js', () => ({
  usePolling: vi.fn(() => ({ data: null, connectionLost: false })),
}));

import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';

function submitScratch(result, fields) {
  act(() => result.current.setMethod('scratch'));
  act(() => result.current.updateField('name', 'Lentejas al curry'));
  act(() => result.current.updateField('category', 'legume'));
  for (const [field, value] of Object.entries(fields)) {
    act(() => result.current.updateField(field, value));
  }
  act(() => result.current.submit());
}

function submittedRecipe(onSubmit) {
  return onSubmit.mock.calls[0][0].recipe;
}

describe('useRecipeAuthoring - estimated time on the wire', () => {
  it('sends estimatedTime as a number, not the raw input string (E2)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'candidate', onSubmit }));

    submitScratch(result, { estimatedTime: '45' });

    expect(submittedRecipe(onSubmit).estimatedTime).toBe(45);
  });

  it('sends estimatedTime as null when the field is left empty (E2)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'candidate', onSubmit }));

    submitScratch(result, { servings: '4' });

    expect(submittedRecipe(onSubmit).estimatedTime).toBeNull();
  });

  it('re-sends an edited recipe estimatedTime as a number, not a string (E2, edit path)', () => {
    const onSubmit = vi.fn();
    const initialRecipe = {
      name: 'Receta r-1',
      category: 'legume',
      servings: 2,
      estimatedTime: 30,
      ingredients: [],
      tools: [],
      procedure: [],
    };
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'library', onSubmit, initialRecipe }),
    );

    act(() => result.current.setMethod('scratch'));
    act(() => result.current.submit());

    expect(submittedRecipe(onSubmit).estimatedTime).toBe(30);
  });

  it('seeds the edit form with the minute count as text, like Comensales (E2)', () => {
    const initialRecipe = {
      name: 'Receta r-1',
      category: 'legume',
      servings: 2,
      estimatedTime: 30,
      ingredients: [],
      tools: [],
      procedure: [],
    };
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'library', onSubmit: vi.fn(), initialRecipe }),
    );

    expect(result.current.form.estimatedTime).toBe('30');
  });
});

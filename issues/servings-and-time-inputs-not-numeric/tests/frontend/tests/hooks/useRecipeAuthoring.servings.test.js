// @vitest-environment jsdom
// Issue 4 (E1, E2, E7): `servings` is a JSON number on the wire
// (rest_api_contract.md 3.1), `estimatedTime` stays the author's free text
// (FR-LIB-03 / G-85).
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

    submitScratch(result, { estimatedTime: '45 min' });

    expect(submittedRecipe(onSubmit).servings).toBeNull();
  });

  it('re-sends an edited recipe servings as a number, not a string (E1, edit path)', () => {
    const onSubmit = vi.fn();
    const initialRecipe = {
      name: 'Receta r-1',
      category: 'legume',
      servings: 2,
      estimatedTime: '30 min',
      ingredients: [],
      tools: [],
      procedure: [],
    };
    const { result } = renderHook(() =>
      useRecipeAuthoring({ mode: 'library', onSubmit, initialRecipe }),
    );

    act(() => result.current.setMethod('scratch'));
    act(() => result.current.submit());

    expect(submittedRecipe(onSubmit).servings).toBe(2);
  });

  it('sends estimatedTime as the typed free text, unit included (E7, G-85)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'candidate', onSubmit }));

    submitScratch(result, { servings: '4', estimatedTime: '45 min' });

    expect(submittedRecipe(onSubmit).estimatedTime).toBe('45 min');
  });

  it('never parses estimatedTime into a number (E7, G-85)', () => {
    const onSubmit = vi.fn();
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'candidate', onSubmit }));

    submitScratch(result, { servings: '4', estimatedTime: '90' });

    expect(submittedRecipe(onSubmit).estimatedTime).toBe('90');
  });
});

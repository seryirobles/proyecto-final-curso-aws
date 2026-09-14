// @vitest-environment jsdom
import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch, ApiError } from '../../src/api/client.js';
import { useRecipeDetail, normalizeRecipeDetail } from '../../src/hooks/useRecipeDetail.js';

const FLAT_RECIPE = {
  name: 'Lentejas al curry',
  category: 'legume',
  servings: 4,
  estimatedTime: '45 min',
  ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
  tools: ['olla'],
  procedure: ['Sofreír la cebolla.'],
};

describe('useRecipeDetail', () => {
  afterEach(() => vi.clearAllMocks());

  it('opens with an already-held recipe and does not fetch', () => {
    const { result } = renderHook(() => useRecipeDetail({ recipe: FLAT_RECIPE }));

    expect(result.current).toEqual({ recipe: FLAT_RECIPE, isLoading: false, error: null });
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it('fetches a week candidate by id when only ids are passed (T18)', async () => {
    apiFetch.mockResolvedValue({ id: 'c1', author: 'Marta', recipe: FLAT_RECIPE });

    const { result } = renderHook(() =>
      useRecipeDetail({ weekId: '2026-W34', day: 1, slot: 2, candidateId: 'c1' }),
    );

    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(apiFetch).toHaveBeenCalledWith('/v1/weeks/2026-W34/days/1/slots/2/candidates/c1');
    expect(result.current.recipe).toMatchObject({ name: 'Lentejas al curry', author: 'Marta' });
    // Regression: the effect must key off source's primitive fields, not
    // its object identity, or a fresh `{ ... }` literal per render loops.
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });

  it('sets error to a rejected fetch detail, es-ES verbatim (R15)', async () => {
    apiFetch.mockRejectedValue(
      new ApiError({ status: 404, code: 'NOT_FOUND', detail: 'No existe.' }),
    );

    const { result } = renderHook(() =>
      useRecipeDetail({ weekId: '2026-W34', day: 1, slot: 2, candidateId: 'c1' }),
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe('No existe.');
    expect(result.current.recipe).toBeNull();
  });

  it('fetches a library recipe by id when only a recipeId is passed (T18)', async () => {
    apiFetch.mockResolvedValue({ id: 'r1', author: 'Iker', ...FLAT_RECIPE, name: 'Tortilla' });

    const { result } = renderHook(() => useRecipeDetail({ recipeId: 'r1' }));

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(apiFetch).toHaveBeenCalledWith('/v1/library/recipes/r1');
    expect(result.current.recipe.name).toBe('Tortilla');
  });
});

describe('normalizeRecipeDetail', () => {
  it('flattens a candidate payload nested under recipe', () => {
    expect(normalizeRecipeDetail({ id: 'c1', author: 'Marta', recipe: FLAT_RECIPE })).toMatchObject(
      {
        name: 'Lentejas al curry',
        author: 'Marta',
      },
    );
  });

  it('accepts an already-flat library payload', () => {
    expect(normalizeRecipeDetail({ id: 'r1', author: 'Iker', ...FLAT_RECIPE })).toMatchObject({
      name: 'Lentejas al curry',
      author: 'Iker',
    });
  });
});

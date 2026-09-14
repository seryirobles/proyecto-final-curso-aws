// Recipe detail state (T18, design.md section 5, 5.1): opens with an
// already-held recipe, or fetches one of the two single-recipe reads when
// only an id is passed. Full reasoning: progress/impl_frontend_spa.md.

import { useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { MESSAGES } from '../messages/index.js';

// AP10 nests the recipe under `recipe`; AP15 flattens it (routing.py
// `_get_candidate` / `_encode_library_entry`). One shape out either way
// (R4, R5).
export function normalizeRecipeDetail(payload) {
  if (!payload) return null;
  const recipe = payload.recipe ?? payload;
  return {
    name: recipe.name,
    category: recipe.category,
    servings: recipe.servings,
    estimatedTime: recipe.estimatedTime,
    ingredients: recipe.ingredients ?? [],
    tools: recipe.tools ?? [],
    procedure: recipe.procedure ?? [],
    author: payload.author,
  };
}

function resolveUrl({ weekId, day, slot, candidateId, recipeId }) {
  if (candidateId != null) {
    return `/v1/weeks/${weekId}/days/${day}/slots/${slot}/candidates/${candidateId}`;
  }
  return `/v1/library/recipes/${recipeId}`;
}

export function useRecipeDetail(source) {
  // Deps below are `source`'s own primitive fields, never `source` itself -
  // a fresh object literal per render (every call site here) would re-run
  // this effect forever otherwise. progress/impl_frontend_spa.md.
  const heldRecipe = source?.recipe ?? null;
  const weekId = source?.weekId;
  const day = source?.day;
  const slot = source?.slot;
  const candidateId = source?.candidateId;
  const recipeId = source?.recipeId;
  const needsFetch = source != null && !heldRecipe;
  const requestKey = needsFetch
    ? JSON.stringify({ weekId, day, slot, candidateId, recipeId })
    : null;

  // Keyed by the request it answers, so `isLoading` is a derived comparison
  // below rather than a second, separately-set state value (no synchronous
  // setState in the effect body - react-hooks/set-state-in-effect).
  const [fetched, setFetched] = useState({ key: null, recipe: null });
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!needsFetch) return undefined;
    let cancelled = false;
    apiFetch(resolveUrl({ weekId, day, slot, candidateId, recipeId })).then(
      (payload) => {
        if (cancelled) return;
        setFetched({ key: requestKey, recipe: normalizeRecipeDetail(payload) });
        setError(null);
      },
      (err) => {
        if (cancelled) return;
        // R15 / design.md section 4.1: surface `error.detail` verbatim.
        setFetched({ key: requestKey, recipe: null });
        setError(err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR);
      },
    );
    return () => {
      cancelled = true;
    };
  }, [needsFetch, requestKey, weekId, day, slot, candidateId, recipeId]);

  if (heldRecipe) return { recipe: heldRecipe, isLoading: false, error: null };
  if (source == null) return { recipe: null, isLoading: false, error: null };
  return { recipe: fetched.recipe, isLoading: fetched.key !== requestKey, error };
}

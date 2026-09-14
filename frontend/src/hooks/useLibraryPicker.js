// Library search/filter state (T25, design.md section 5): shared by the
// library view and every recipe-picker embed (R11-R14). Polls the fixed
// unfiltered URI, filters client-side - see progress/impl_frontend_spa.md,
// "Library slice - Fix round 1" (F1) for why.

import { useCallback, useMemo, useState } from 'react';
import { usePolling } from './usePolling.js';

const LIBRARY_RECIPES_URL = '/v1/library/recipes';

function emptyFilters() {
  return { name: '', category: '' }; // R14 - exactly these two keys, nothing else
}

function matchesFilters(recipe, { name, category }) {
  if (name && !recipe.name.toLocaleLowerCase('es-ES').includes(name.toLocaleLowerCase('es-ES'))) {
    return false;
  }
  if (category && recipe.category !== category) return false;
  return true;
}

export function useLibraryPicker({ enabled = true } = {}) {
  const [filters, setFilters] = useState(emptyFilters);

  const setName = useCallback((name) => {
    setFilters((current) => ({ ...current, name })); // R11
  }, []);
  const setCategory = useCallback((category) => {
    setFilters((current) => ({ ...current, category })); // R13
  }, []);

  const poll = usePolling(LIBRARY_RECIPES_URL, undefined, { enabled });
  const allRecipes = useMemo(() => poll.data?.recipes ?? [], [poll.data]);
  const recipes = useMemo(
    () => allRecipes.filter((recipe) => matchesFilters(recipe, filters)),
    [allRecipes, filters],
  );

  return {
    filters,
    setName,
    setCategory,
    recipes,
    allRecipes, // unfiltered result list, for the new-pin recipe-picker control

    isLoading: poll.data === null,
    connectionLost: poll.connectionLost,
    applyMutationMarker: poll.applyMutationMarker, // design.md section 4.2
  };
}

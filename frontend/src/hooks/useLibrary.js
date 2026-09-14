// Library view state (T28, design.md section 5 Screens table): filtering
// (useLibraryPicker), add/edit routed through useRecipeAuthoring, remove
// gated by useConfirm (R18), recipe detail via the shared T18 opener (R5).

import { useCallback, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { useLibraryPicker } from './useLibraryPicker.js';
import { useRecipeAuthoring } from './useRecipeAuthoring.js';
import { useConfirm } from './useConfirm.js';
import { useRecipeDetail, normalizeRecipeDetail } from './useRecipeDetail.js';
import { parseMarker } from '../realtime/etag.js';
import { MESSAGES } from '../messages/index.js';

// R15 / design.md section 4.1: surface `error.detail` verbatim, never a
// composed message.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

export function useLibrary({ active = true } = {}) {
  const picker = useLibraryPicker({ enabled: active });
  const confirm = useConfirm();
  // Holds the whole recipe, not just its id, so useRecipeAuthoring can seed
  // the edit form from real content instead of opening blank (F4 fix round 1).
  const [editingRecipe, setEditingRecipe] = useState(null);
  const editingId = editingRecipe?.id ?? null;
  const [isAuthoringOpen, setIsAuthoringOpen] = useState(false);
  const [detailSource, setDetailSource] = useState(null);
  const [error, setError] = useState(null);
  const detail = useRecipeDetail(detailSource);

  const handleSubmit = useCallback(
    async ({ recipe }) => {
      const path = editingId ? `/v1/library/recipes/${editingId}` : '/v1/library/recipes';
      try {
        let marker = null;
        await apiFetch(path, {
          method: editingId ? 'PUT' : 'POST',
          body: { source: 'manual', recipe },
          onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
        });
        picker.applyMutationMarker(marker); // design.md section 4.2
        setError(null);
        setIsAuthoringOpen(false);
        setEditingRecipe(null);
      } catch (err) {
        setError(toDetail(err));
      }
    },
    [editingId, picker],
  );

  const authoring = useRecipeAuthoring({
    mode: 'library',
    onSubmit: handleSubmit,
    initialRecipe: editingRecipe,
    active,
  });

  const openAdd = useCallback(() => {
    setEditingRecipe(null);
    setIsAuthoringOpen(true);
  }, []);
  const openEdit = useCallback((recipe) => {
    setEditingRecipe(recipe);
    setIsAuthoringOpen(true);
  }, []);
  const closeAuthoring = useCallback(() => setIsAuthoringOpen(false), []);

  const remove = useCallback(
    (recipeId) => {
      confirm.requestConfirm(MESSAGES.CONFIRM_REMOVE_LIBRARY_RECIPE, async () => {
        // R18
        try {
          let marker = null;
          await apiFetch(`/v1/library/recipes/${recipeId}`, {
            method: 'DELETE',
            onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
          });
          picker.applyMutationMarker(marker);
          setError(null);
        } catch (err) {
          setError(toDetail(err));
        }
      });
    },
    [confirm, picker],
  );

  const openDetail = useCallback(
    (recipe) => setDetailSource({ recipe: normalizeRecipeDetail(recipe) }),
    [],
  );
  const closeDetail = useCallback(() => setDetailSource(null), []);

  return {
    recipes: picker.recipes,
    filters: picker.filters,
    setName: picker.setName,
    setCategory: picker.setCategory,
    isLoading: picker.isLoading,
    connectionLost: picker.connectionLost,
    isAuthoringOpen,
    isEditing: editingId != null,
    authoring,
    openAdd,
    openEdit,
    closeAuthoring,
    remove,
    confirm,
    openDetail,
    detail: detail.recipe,
    isDetailLoading: detail.isLoading,
    detailError: detail.error,
    closeDetail,
    error,
  };
}

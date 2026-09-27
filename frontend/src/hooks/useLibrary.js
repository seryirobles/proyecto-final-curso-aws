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
import { DAY_LABELS, SLOT_LABELS } from '../domain/labels.js';

// R15 / design.md section 4.1: surface `error.detail` verbatim, never a
// composed message.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

// R2: renders one affected pin as "<day> · <slot>" (design.md section 4).
function formatPin(pin) {
  return `${DAY_LABELS[pin.day]} · ${SLOT_LABELS[pin.slot]}`;
}

function composeCascadeMessage(pins) {
  const list = pins.map(formatPin).join(', ');
  return `${MESSAGES.LIBRARY_REMOVE_PIN_CASCADE_WARNING} ${list}. ${MESSAGES.LIBRARY_REMOVE_PIN_CASCADE_CONFIRM}`;
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
        picker.refetchNow(); // issue new-recipe-not-shown-in-library, E1/E2
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

  // T2: shared by the first DELETE attempt and the R3 cascade retry - only
  // the query string differs (design.md section 4).
  const deleteRecipe = useCallback(
    async (recipeId, { confirmCascade }) => {
      const query = confirmCascade ? '?confirmCascade=true' : '';
      let marker = null;
      await apiFetch(`/v1/library/recipes/${recipeId}${query}`, {
        method: 'DELETE',
        onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
      });
      picker.applyMutationMarker(marker);
      picker.refetchNow(); // issue ui-not-reflecting-mutations, E1 / R6
      setError(null);
    },
    [picker],
  );

  const remove = useCallback(
    (recipeId) => {
      confirm.requestConfirm(MESSAGES.CONFIRM_REMOVE_LIBRARY_RECIPE, async () => {
        // R18
        try {
          await deleteRecipe(recipeId, { confirmCascade: false });
        } catch (err) {
          if (err instanceof ApiError && err.code === 'PIN_RULES_AFFECTED') {
            // R1, R2: re-arm the same confirm instance with the cascade prompt.
            confirm.requestConfirm(composeCascadeMessage(err.details?.pins ?? []), async () => {
              try {
                await deleteRecipe(recipeId, { confirmCascade: true }); // R3
              } catch (retryErr) {
                setError(toDetail(retryErr)); // R7 fallback, same path as any other failure
              }
            });
          } else {
            setError(toDetail(err)); // R7
          }
        }
      });
    },
    [confirm, deleteRecipe],
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

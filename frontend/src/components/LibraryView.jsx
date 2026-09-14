// The library screen (T29; design.md section 5, Screens table): recipe
// list with per-recipe author (FR-CAND-04/FR-LIB-01 field, no attribution
// logic here), add/edit/remove, EmptyState for zero results (R9, R10, R19).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { EmptyState } from './EmptyState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { RecipeDetailView } from './RecipeDetailView.jsx';
import { RecipeAuthoringForm } from './RecipeAuthoringForm.jsx';
import { LibraryFilters } from './LibraryFilters.jsx';

export function LibraryView({
  recipes,
  filters,
  setName,
  setCategory,
  isLoading,
  isAuthoringOpen,
  authoring,
  openAdd,
  openEdit,
  closeAuthoring,
  remove,
  confirm,
  openDetail,
  detail,
  detailError,
  closeDetail,
  error,
}) {
  if (isLoading) return <LoadingState />;

  return (
    <div>
      <h2 style={{ margin: tokens.space.none }}>{MESSAGES.LIBRARY_VIEW_TITLE}</h2>
      {error ? <p style={{ color: tokens.color.ink, padding: tokens.space.md }}>{error}</p> : null}

      <LibraryFilters filters={filters} setName={setName} setCategory={setCategory} />
      <button type="button" onClick={openAdd}>
        {MESSAGES.LIBRARY_VIEW_ADD}
      </button>

      {recipes.length === 0 ? (
        <EmptyState message={MESSAGES.LIBRARY_VIEW_EMPTY} />
      ) : (
        <ul>
          {recipes.map((recipe) => (
            <li key={recipe.id}>
              <button
                type="button"
                onClick={() => openDetail(recipe)}
                style={{
                  color: tokens.color.terra,
                  backgroundColor: 'transparent',
                  border: 'none',
                  padding: tokens.space.none,
                }}
              >
                {recipe.name}
              </button>
              <span style={{ color: tokens.color.ink2 }}> · {recipe.author}</span>
              <button type="button" onClick={() => openEdit(recipe)}>
                {MESSAGES.LIBRARY_VIEW_EDIT}
              </button>
              <button type="button" onClick={() => remove(recipe.id)}>
                {MESSAGES.LIBRARY_VIEW_REMOVE}
              </button>
            </li>
          ))}
        </ul>
      )}

      {isAuthoringOpen ? (
        <div>
          <RecipeAuthoringForm {...authoring} />
          <button type="button" onClick={closeAuthoring}>
            {MESSAGES.RECIPE_DETAIL_CLOSE}
          </button>
        </div>
      ) : null}

      <ConfirmDialog
        pending={confirm.pending}
        onConfirm={confirm.confirm}
        onCancel={confirm.cancel}
      />

      {detail || detailError ? (
        <RecipeDetailView recipe={detail} error={detailError} onClose={closeDetail} />
      ) : null}
    </div>
  );
}

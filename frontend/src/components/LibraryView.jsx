// The library screen (T29; design.md section 5, Screens table): recipe
// list with per-recipe author (FR-CAND-04/FR-LIB-01 field, no attribution
// logic here), add/edit/remove, EmptyState for zero results (R9, R10, R19).

// Card-grid layout, category-color dot, icon-button row (T85, design.md
// 10.6). No "IA" badge: same wall as T82 (MealCard) - see
// progress/impl_frontend_spa.md, "Tier E - library".

import { tokens } from '../tokens/index.js';
import { secondaryButtonStyle } from '../tokens/controlStyles.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_COLORS } from '../domain/labels.js';
import { EmptyState } from './EmptyState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { RecipeDetailView } from './RecipeDetailView.jsx';
import { RecipeAuthoringForm } from './RecipeAuthoringForm.jsx';
import { LibraryFilters } from './LibraryFilters.jsx';

function EditIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 20h4L19 9l-4-4L4 16z" />
      <path d="M14 5l4 4" />
    </svg>
  );
}

function DeleteIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    >
      <path d="M4 7h16M9 7V4.5h6V7M6.5 7l1 13h9l1-13" />
    </svg>
  );
}

const iconButtonStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: tokens.space.xs,
  border: `1px solid ${tokens.color.line2}`,
  backgroundColor: tokens.color.surface2,
  color: tokens.color.ink2,
  borderRadius: tokens.radius.sm,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  fontSize: tokens.fontSize.xs,
  fontWeight: 700,
};

const addButtonStyle = {
  border: 'none',
  backgroundColor: tokens.color.terra,
  color: tokens.color.surface,
  borderRadius: tokens.radius.sm,
  padding: `${tokens.space.sm} ${tokens.space.md}`,
  fontWeight: 700,
  fontSize: tokens.fontSize.sm,
};

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
      <h2
        style={{
          margin: tokens.space.none,
          fontFamily: tokens.fontFamily.heading,
          fontSize: tokens.fontSize.xl,
        }}
      >
        {MESSAGES.LIBRARY_VIEW_TITLE}
      </h2>
      {error ? (
        <p
          style={{
            color: tokens.color.honey,
            backgroundColor: tokens.color.honeySoft,
            borderRadius: tokens.radius.sm,
            padding: tokens.space.md,
            marginTop: tokens.space.sm,
          }}
        >
          {error}
        </p>
      ) : null}

      <div style={{ marginTop: tokens.space.md }}>
        <LibraryFilters filters={filters} setName={setName} setCategory={setCategory} />
      </div>
      <button type="button" onClick={openAdd} style={addButtonStyle}>
        {MESSAGES.LIBRARY_VIEW_ADD}
      </button>

      {recipes.length === 0 ? (
        <EmptyState message={MESSAGES.LIBRARY_VIEW_EMPTY} />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 240px), 1fr))',
            gap: tokens.space.md,
            marginTop: tokens.space.md,
          }}
        >
          {recipes.map((recipe) => (
            <div
              key={recipe.id}
              style={{
                backgroundColor: tokens.color.surface,
                border: `1px solid ${tokens.color.line}`,
                borderRadius: tokens.radius.md,
                boxShadow: tokens.shadow.sm,
                padding: tokens.space.md,
                display: 'flex',
                flexDirection: 'column',
                gap: tokens.space.sm,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: tokens.space.xs }}>
                <span
                  style={{
                    width: '9px',
                    height: '9px',
                    borderRadius: tokens.radius.pill,
                    backgroundColor: tokens.color[CATEGORY_COLORS[recipe.category]],
                    flex: 'none',
                  }}
                />
                <button
                  type="button"
                  onClick={() => openDetail(recipe)}
                  style={{
                    color: tokens.color.terra,
                    backgroundColor: 'transparent',
                    border: 'none',
                    padding: tokens.space.none,
                    fontFamily: tokens.fontFamily.heading,
                    fontSize: tokens.fontSize.sm,
                    textAlign: 'left',
                  }}
                >
                  {recipe.name}
                </button>
              </div>
              <span
                style={{
                  fontFamily: tokens.fontFamily.label,
                  fontSize: tokens.fontSize.xs,
                  color: tokens.color.ink3,
                }}
              >
                {recipe.author}
              </span>
              <div style={{ display: 'flex', gap: tokens.space.xs }}>
                <button type="button" onClick={() => openEdit(recipe)} style={iconButtonStyle}>
                  <EditIcon />
                  {MESSAGES.LIBRARY_VIEW_EDIT}
                </button>
                <button type="button" onClick={() => remove(recipe.id)} style={iconButtonStyle}>
                  <DeleteIcon />
                  {MESSAGES.LIBRARY_VIEW_REMOVE}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isAuthoringOpen ? (
        <div>
          <RecipeAuthoringForm {...authoring} />
          <button
            type="button"
            onClick={closeAuthoring}
            style={{ ...secondaryButtonStyle, marginTop: tokens.space.sm }}
          >
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

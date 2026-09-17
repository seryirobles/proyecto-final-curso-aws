// Search input + category select + result list (T26, design.md section 5):
// pure function of useLibraryPicker's state, reused across R12's call sites.

// Card-grid result list (T85, design.md 10.6), replacing the plain <ul> -
// mined from the prototype's library grid, not ported.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_COLORS } from '../domain/labels.js';
import { EmptyState } from './EmptyState.jsx';
import { LibraryFilters } from './LibraryFilters.jsx';

function selectButtonStyle(isSelected) {
  return {
    border: `1px solid ${isSelected ? tokens.color.terra : tokens.color.line2}`,
    backgroundColor: isSelected ? tokens.color.terraSoft : tokens.color.surface2,
    color: isSelected ? tokens.color.terra : tokens.color.ink2,
    borderRadius: tokens.radius.sm,
    padding: `${tokens.space.xs} ${tokens.space.sm}`,
    fontSize: tokens.fontSize.xs,
    fontWeight: 700,
  };
}

export function LibraryRecipePicker({
  filters,
  setName,
  setCategory,
  recipes,
  selectedRecipeId,
  onSelect,
}) {
  return (
    <div>
      <LibraryFilters filters={filters} setName={setName} setCategory={setCategory} />

      {recipes.length === 0 ? (
        <EmptyState message={MESSAGES.LIBRARY_PICKER_EMPTY} />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 200px), 1fr))',
            gap: tokens.space.sm,
          }}
        >
          {recipes.map((recipe) => {
            const isSelected = recipe.id === selectedRecipeId;
            return (
              <div
                key={recipe.id}
                style={{
                  backgroundColor: isSelected ? tokens.color.terraSoft : tokens.color.surface,
                  border: `1px solid ${tokens.color.line}`,
                  borderRadius: tokens.radius.md,
                  boxShadow: tokens.shadow.sm,
                  padding: tokens.space.sm,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: tokens.space.xs,
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
                  <span
                    style={{ fontFamily: tokens.fontFamily.heading, fontSize: tokens.fontSize.sm }}
                  >
                    {recipe.name}
                  </span>
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
                <button
                  type="button"
                  onClick={() => onSelect(recipe.id)}
                  style={selectButtonStyle(isSelected)}
                >
                  {isSelected ? MESSAGES.LIBRARY_PICKER_SELECTED : MESSAGES.LIBRARY_PICKER_SELECT}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Search input + category select + result list (T26, design.md section 5):
// pure function of useLibraryPicker's state, reused across R12's call sites.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { EmptyState } from './EmptyState.jsx';
import { LibraryFilters } from './LibraryFilters.jsx';

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
        <ul>
          {recipes.map((recipe) => (
            <li key={recipe.id}>
              <span>{recipe.name}</span>
              <span style={{ color: tokens.color.ink2 }}> · {recipe.author}</span>
              <button type="button" onClick={() => onSelect(recipe.id)}>
                {recipe.id === selectedRecipeId
                  ? MESSAGES.LIBRARY_PICKER_SELECTED
                  : MESSAGES.LIBRARY_PICKER_SELECT}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

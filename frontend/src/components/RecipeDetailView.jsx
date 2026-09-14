// Recipe detail: ingredients, tools, procedure, time, servings (R4, T19).
// Pure function of `recipe` (already-resolved by `useRecipeDetail`, T18).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { UNIT_LABELS, CATEGORY_LABELS } from '../domain/labels.js';
import { formatNumber } from '../locale.js';

export function RecipeDetailView({ recipe, error, onClose }) {
  if (!recipe) {
    // R15 / design.md section 4.1: still render `error.detail` when the
    // fetch that would have produced `recipe` failed instead.
    if (!error) return null;
    return (
      <div
        style={{
          padding: tokens.space.lg,
          backgroundColor: tokens.color.surface,
          color: tokens.color.ink,
        }}
      >
        <button type="button" onClick={onClose}>
          {MESSAGES.RECIPE_DETAIL_CLOSE}
        </button>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: tokens.space.lg,
        backgroundColor: tokens.color.surface,
        color: tokens.color.ink,
      }}
    >
      <button type="button" onClick={onClose}>
        {MESSAGES.RECIPE_DETAIL_CLOSE}
      </button>
      <h2 style={{ margin: tokens.space.none }}>{recipe.name}</h2>
      <p style={{ color: tokens.color.ink2 }}>{CATEGORY_LABELS[recipe.category]}</p>
      <p>
        {MESSAGES.RECIPE_DETAIL_SERVINGS}:{' '}
        {recipe.servings != null ? formatNumber(recipe.servings) : ''}
      </p>
      <p>
        {MESSAGES.RECIPE_DETAIL_ESTIMATED_TIME}: {recipe.estimatedTime}
      </p>

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RECIPE_DETAIL_INGREDIENTS}</h3>
      <ul>
        {recipe.ingredients.map((ingredient) => (
          <li key={ingredient.name}>
            {ingredient.name} · {formatNumber(ingredient.quantity)} {UNIT_LABELS[ingredient.unit]}
          </li>
        ))}
      </ul>

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RECIPE_DETAIL_TOOLS}</h3>
      <ul>
        {recipe.tools.map((tool) => (
          <li key={tool}>{tool}</li>
        ))}
      </ul>

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RECIPE_DETAIL_PROCEDURE}</h3>
      <ol>
        {recipe.procedure.map((step, index) => (
          <li key={index}>{step}</li>
        ))}
      </ol>
    </div>
  );
}

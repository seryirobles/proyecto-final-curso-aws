// Recipe detail: ingredients, tools, procedure, time, servings (R4, T19).
// Pure function of `recipe` (already-resolved by `useRecipeDetail`, T18).

// Slide-up-sheet shape, pill badges, numbered steps (T83, design.md 10.6) -
// mined from the prototype's bottom sheet, not ported.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { UNIT_LABELS, CATEGORY_LABELS } from '../domain/labels.js';
import { formatNumber } from '../locale.js';

const sectionLabelStyle = {
  fontFamily: tokens.fontFamily.label,
  fontSize: tokens.fontSize.xs,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  color: tokens.color.terraDeep,
  marginBottom: tokens.space.sm,
};

const pillStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  fontSize: tokens.fontSize.xs,
  fontWeight: 600,
  backgroundColor: tokens.color.surface2,
  border: `1px solid ${tokens.color.line}`,
  borderRadius: tokens.radius.pill,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
};

function CloseIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
    >
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

function Sheet({ children }) {
  return (
    <div
      data-testid="recipe-detail-backdrop"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: tokens.color.backdrop,
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '560px',
          maxHeight: '90vh',
          overflowY: 'auto',
          backgroundColor: tokens.color.surface,
          color: tokens.color.ink,
          borderRadius: `${tokens.radius.lg} ${tokens.radius.lg} 0 0`,
          boxShadow: tokens.shadow.lg,
          padding: tokens.space.lg,
        }}
      >
        {children}
      </div>
    </div>
  );
}

function CloseButton({ onClose }) {
  return (
    <button
      type="button"
      onClick={onClose}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: tokens.space.xs,
        border: `1px solid ${tokens.color.line2}`,
        backgroundColor: tokens.color.surface2,
        color: tokens.color.ink2,
        borderRadius: tokens.radius.sm,
        padding: `${tokens.space.xs} ${tokens.space.sm}`,
        fontSize: tokens.fontSize.xs,
      }}
    >
      <CloseIcon />
      {MESSAGES.RECIPE_DETAIL_CLOSE}
    </button>
  );
}

export function RecipeDetailView({ recipe, error, onClose }) {
  if (!recipe) {
    // R15 / design.md section 4.1: still render `error.detail` when the
    // fetch that would have produced `recipe` failed instead.
    if (!error) return null;
    return (
      <Sheet>
        <CloseButton onClose={onClose} />
        <p style={{ marginTop: tokens.space.md }}>{error}</p>
      </Sheet>
    );
  }

  return (
    <Sheet>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: tokens.space.sm,
          marginBottom: tokens.space.md,
        }}
      >
        <h2
          style={{
            margin: tokens.space.none,
            fontFamily: tokens.fontFamily.heading,
            fontSize: tokens.fontSize.lg,
          }}
        >
          {recipe.name}
        </h2>
        <CloseButton onClose={onClose} />
      </div>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: tokens.space.xs,
          marginBottom: tokens.space.md,
        }}
      >
        <span style={pillStyle}>{CATEGORY_LABELS[recipe.category]}</span>
        <span style={pillStyle}>
          {MESSAGES.RECIPE_DETAIL_SERVINGS}:{' '}
          {recipe.servings != null ? formatNumber(recipe.servings) : ''}
        </span>
        <span style={pillStyle}>
          {MESSAGES.RECIPE_DETAIL_ESTIMATED_TIME}: {recipe.estimatedTime}
        </span>
      </div>

      <p style={sectionLabelStyle}>{MESSAGES.RECIPE_DETAIL_INGREDIENTS}</p>
      <div style={{ marginBottom: tokens.space.lg }}>
        {recipe.ingredients.map((ingredient) => (
          <div
            key={ingredient.name}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: tokens.space.sm,
              padding: `${tokens.space.xs} 0`,
              borderBottom: `1px solid ${tokens.color.line}`,
            }}
          >
            <span>
              {ingredient.name} · {formatNumber(ingredient.quantity)} {UNIT_LABELS[ingredient.unit]}
            </span>
          </div>
        ))}
      </div>

      <p style={sectionLabelStyle}>{MESSAGES.RECIPE_DETAIL_TOOLS}</p>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: tokens.space.xs,
          marginBottom: tokens.space.lg,
        }}
      >
        {recipe.tools.map((tool) => (
          <span key={tool} style={pillStyle}>
            {tool}
          </span>
        ))}
      </div>

      <p style={sectionLabelStyle}>{MESSAGES.RECIPE_DETAIL_PROCEDURE}</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: tokens.space.sm }}>
        {recipe.procedure.map((step, index) => (
          <div key={index} style={{ display: 'flex', gap: tokens.space.sm }}>
            <span
              style={{
                width: '24px',
                height: '24px',
                flex: 'none',
                borderRadius: tokens.radius.pill,
                backgroundColor: tokens.color.terraSoft,
                color: tokens.color.terraDeep,
                fontWeight: 700,
                fontSize: tokens.fontSize.xs,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {index + 1}
            </span>
            <span>{step}</span>
          </div>
        ))}
      </div>
    </Sheet>
  );
}

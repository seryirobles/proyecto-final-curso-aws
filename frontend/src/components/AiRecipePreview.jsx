// The previewed AI recipe with accept, discard and regenerate (feature 28,
// R34). Pure function of `recipe` (the wire shape `result` carries).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { UNIT_LABELS, CATEGORY_LABELS } from '../domain/labels.js';
import { formatNumber } from '../locale.js';
import { primaryButtonStyle, secondaryButtonStyle } from '../tokens/controlStyles.js';

const sectionLabelStyle = {
  fontFamily: tokens.fontFamily.label,
  fontSize: tokens.fontSize.xs,
  color: tokens.color.terraDeep,
  margin: `${tokens.space.sm} 0 ${tokens.space.xs}`,
};

export function AiRecipePreview({ recipe, onAccept, onDiscard, onRegenerate }) {
  return (
    <div
      style={{
        marginTop: tokens.space.md,
        padding: tokens.space.md,
        backgroundColor: tokens.color.aubSoft,
        border: `1px solid ${tokens.color.aub}`,
        borderRadius: tokens.radius.md,
      }}
    >
      <p style={sectionLabelStyle}>{MESSAGES.AI_PREVIEW_TITLE}</p>
      <h3 style={{ margin: tokens.space.none, fontFamily: tokens.fontFamily.heading }}>
        {recipe.name}
      </h3>
      <p style={{ color: tokens.color.ink2, fontSize: tokens.fontSize.xs }}>
        {CATEGORY_LABELS[recipe.category]}
      </p>

      <p style={sectionLabelStyle}>{MESSAGES.RECIPE_DETAIL_INGREDIENTS}</p>
      {recipe.ingredients.map((ingredient, index) => (
        <div key={index}>
          {ingredient.name} · {formatNumber(ingredient.quantity)} {UNIT_LABELS[ingredient.unit]}
        </div>
      ))}

      <p style={sectionLabelStyle}>{MESSAGES.RECIPE_DETAIL_TOOLS}</p>
      <div>{recipe.tools.join(', ')}</div>

      <p style={sectionLabelStyle}>{MESSAGES.RECIPE_DETAIL_PROCEDURE}</p>
      {recipe.procedure.map((step, index) => (
        <div key={index}>
          {index + 1}. {step}
        </div>
      ))}

      <div style={{ display: 'flex', gap: tokens.space.sm, marginTop: tokens.space.md }}>
        <button type="button" onClick={onAccept} style={primaryButtonStyle(false)}>
          {MESSAGES.AI_ACCEPT}
        </button>
        <button type="button" onClick={onRegenerate} style={secondaryButtonStyle}>
          {MESSAGES.AI_REGENERATE}
        </button>
        <button type="button" onClick={onDiscard} style={secondaryButtonStyle}>
          {MESSAGES.AI_DISCARD}
        </button>
      </div>
    </div>
  );
}

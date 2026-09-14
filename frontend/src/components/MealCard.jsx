// One candidate meal (structural, R1-R5; design.md section 5). Reused for a
// regular candidate and for a slot's definitive meal alike (R5) - the caller
// passes `isDefinitive`, no separate component exists for that role.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

export function MealCard({ candidate, isDefinitive, onOpenDetail, onPromote, onClear }) {
  return (
    <div
      style={{
        padding: tokens.space.sm,
        marginTop: tokens.space.xs,
        backgroundColor: isDefinitive ? tokens.color.oliveSoft : tokens.color.surface2,
        border: `1px solid ${tokens.color.line}`,
      }}
    >
      <button
        type="button"
        onClick={() => onOpenDetail(candidate)}
        style={{
          color: tokens.color.terra,
          backgroundColor: 'transparent',
          border: 'none',
          padding: tokens.space.none,
        }}
      >
        {candidate.recipe.name}
      </button>
      <p style={{ margin: tokens.space.none, color: tokens.color.ink2 }}>{candidate.author}</p>
      {isDefinitive ? (
        <span style={{ color: tokens.color.olive }}>{MESSAGES.WEEK_PLANNER_DEFINITIVE_BADGE}</span>
      ) : null}
      <div style={{ marginTop: tokens.space.xs }}>
        {isDefinitive ? (
          <button type="button" onClick={onClear}>
            {MESSAGES.WEEK_PLANNER_CLEAR_DEFINITIVE}
          </button>
        ) : (
          <button type="button" onClick={onPromote}>
            {MESSAGES.WEEK_PLANNER_PROMOTE_DEFINITIVE}
          </button>
        )}
      </div>
    </div>
  );
}

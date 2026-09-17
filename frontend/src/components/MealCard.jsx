// One candidate meal (structural, R1-R5; design.md section 5). Reused for a
// regular candidate and for a slot's definitive meal alike (R5) - the caller
// passes `isDefinitive`, no separate component exists for that role.

// No AI-authored ("IA") badge (T82, design.md 10.6): the real candidate has
// no origin field to key it on. See progress/impl_frontend_spa.md, Tier D.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

const actionButtonStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: tokens.space.xs,
  border: 'none',
  backgroundColor: 'transparent',
  borderRadius: tokens.radius.pill,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  fontSize: tokens.fontSize.xs,
  fontWeight: 700,
};

function CheckIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12.5l4.5 4.5 9-10" />
    </svg>
  );
}

function ClearIcon() {
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

export function MealCard({ candidate, isDefinitive, onOpenDetail, onPromote, onClear }) {
  return (
    <div
      style={{
        padding: tokens.space.sm,
        marginTop: tokens.space.xs,
        backgroundColor: isDefinitive ? tokens.color.oliveSoft : tokens.color.surface2,
        border: `1px solid ${tokens.color.line}`,
        borderRadius: tokens.radius.md,
        boxShadow: tokens.shadow.sm,
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
          fontFamily: tokens.fontFamily.heading,
          fontSize: tokens.fontSize.sm,
        }}
      >
        {candidate.recipe.name}
      </button>
      <p
        style={{
          margin: tokens.space.none,
          fontFamily: tokens.fontFamily.label,
          fontSize: tokens.fontSize.xs,
          color: tokens.color.ink2,
        }}
      >
        {candidate.author}
      </p>
      {isDefinitive ? (
        <span
          style={{
            display: 'inline-block',
            marginTop: tokens.space.xs,
            fontSize: tokens.fontSize.xs,
            fontWeight: 700,
            color: tokens.color.olive,
            backgroundColor: tokens.color.oliveSoft,
            borderRadius: tokens.radius.pill,
            padding: `${tokens.space.xs} ${tokens.space.sm}`,
          }}
        >
          {MESSAGES.WEEK_PLANNER_DEFINITIVE_BADGE}
        </span>
      ) : null}
      <div style={{ marginTop: tokens.space.xs }}>
        {isDefinitive ? (
          <button
            type="button"
            onClick={onClear}
            style={{ ...actionButtonStyle, color: tokens.color.ink3 }}
          >
            <ClearIcon />
            {MESSAGES.WEEK_PLANNER_CLEAR_DEFINITIVE}
          </button>
        ) : (
          <button
            type="button"
            onClick={onPromote}
            style={{ ...actionButtonStyle, color: tokens.color.terra }}
          >
            <CheckIcon />
            {MESSAGES.WEEK_PLANNER_PROMOTE_DEFINITIVE}
          </button>
        )}
      </div>
    </div>
  );
}

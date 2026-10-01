// One day's lunch + dinner slots (structural, R1; design.md section 5).
// Empty/loading obligations (R19) render through `EmptyState`.

// Day-card shape + status pill (T81, design.md 10.6) - a presentation-only
// aggregation of the already-fetched slots, not a recomputed domain rule.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { DAY_LABELS, SLOT_LABELS } from '../domain/labels.js';
import { EmptyState } from './EmptyState.jsx';
import { MealCard } from './MealCard.jsx';

const STATUS_STYLES = {
  definitive: {
    label: MESSAGES.WEEK_PLANNER_DAY_STATUS_DEFINITIVE,
    color: tokens.color.olive,
    background: tokens.color.oliveSoft,
  },
  candidates: {
    label: MESSAGES.WEEK_PLANNER_DAY_STATUS_CANDIDATES,
    color: tokens.color.terra,
    background: tokens.color.terraSoft,
  },
  empty: {
    label: MESSAGES.WEEK_PLANNER_DAY_STATUS_EMPTY,
    color: tokens.color.ink3,
    background: tokens.color.surface2,
  },
};

function dayStatus(slots) {
  if (slots.some((slotState) => slotState.definitiveId != null)) return 'definitive';
  if (slots.some((slotState) => slotState.candidates.length > 0)) return 'candidates';
  return 'empty';
}

export function DaySlot({
  day,
  slots,
  onAddCandidate,
  onOpenDetail,
  onPromote,
  onClear,
  onEdit,
  onRemove,
  pending,
}) {
  const status = STATUS_STYLES[dayStatus(slots)];

  return (
    <div
      style={{
        backgroundColor: tokens.color.surface,
        border: `1px solid ${tokens.color.line}`,
        borderRadius: tokens.radius.md,
        boxShadow: tokens.shadow.sm,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: tokens.space.sm,
          padding: tokens.space.sm,
          borderBottom: `1px solid ${tokens.color.line}`,
          backgroundColor: tokens.color.surface2,
        }}
      >
        <p
          style={{
            margin: tokens.space.none,
            fontFamily: tokens.fontFamily.heading,
            color: tokens.color.ink,
          }}
        >
          {DAY_LABELS[day]}
        </p>
        <span
          style={{
            fontSize: tokens.fontSize.xs,
            fontWeight: 700,
            color: status.color,
            backgroundColor: status.background,
            borderRadius: tokens.radius.pill,
            padding: `${tokens.space.xs} ${tokens.space.sm}`,
            flex: 'none',
          }}
        >
          {status.label}
        </span>
      </div>
      <div
        style={{
          padding: tokens.space.sm,
          display: 'flex',
          flexDirection: 'column',
          gap: tokens.space.sm,
        }}
      >
        {slots.map((slotState) => (
          <div key={slotState.slot}>
            <p
              style={{
                margin: tokens.space.none,
                fontFamily: tokens.fontFamily.label,
                fontSize: tokens.fontSize.xs,
                textTransform: 'uppercase',
                color: tokens.color.ink2,
              }}
            >
              {SLOT_LABELS[slotState.slot]}
            </p>
            {slotState.isEmpty ? (
              <EmptyState message={MESSAGES.WEEK_PLANNER_EMPTY_SLOT} />
            ) : (
              slotState.candidates.map((candidate) => (
                <MealCard
                  key={candidate.id}
                  candidate={candidate}
                  isDefinitive={candidate.id === slotState.definitiveId}
                  onOpenDetail={onOpenDetail}
                  onPromote={() => onPromote(day, slotState.slot, candidate.id)}
                  onClear={() => onClear(day, slotState.slot)}
                  onEdit={() => onEdit(day, slotState.slot, candidate)}
                  onRemove={() => onRemove(day, slotState.slot, candidate.id)}
                  isPromoting={pending?.has(`promote:${day}:${slotState.slot}`)}
                  isClearing={pending?.has(`clear:${day}:${slotState.slot}`)}
                  isRemoving={pending?.has(`remove:${candidate.id}`)}
                />
              ))
            )}
            <button
              type="button"
              onClick={() => onAddCandidate(day, slotState.slot)}
              style={{
                width: '100%',
                marginTop: tokens.space.xs,
                border: `1px dashed ${tokens.color.line2}`,
                backgroundColor: 'transparent',
                color: tokens.color.ink2,
                borderRadius: tokens.radius.sm,
                padding: tokens.space.xs,
                fontSize: tokens.fontSize.xs,
              }}
            >
              {MESSAGES.WEEK_PLANNER_ADD_CANDIDATE}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

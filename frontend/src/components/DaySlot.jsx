// One day's lunch + dinner slots (structural, R1; design.md section 5).
// Empty/loading obligations (R19) render through `EmptyState`.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { DAY_LABELS, SLOT_LABELS } from '../domain/labels.js';
import { EmptyState } from './EmptyState.jsx';
import { MealCard } from './MealCard.jsx';

export function DaySlot({ day, slots, onAddCandidate, onOpenDetail, onPromote, onClear }) {
  return (
    <div style={{ padding: tokens.space.sm, border: `1px solid ${tokens.color.line2}` }}>
      <p style={{ margin: tokens.space.none, color: tokens.color.ink }}>{DAY_LABELS[day]}</p>
      {slots.map((slotState) => (
        <div key={slotState.slot} style={{ marginTop: tokens.space.sm }}>
          <p style={{ margin: tokens.space.none, color: tokens.color.ink2 }}>
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
              />
            ))
          )}
          <button type="button" onClick={() => onAddCandidate(day, slotState.slot)}>
            {MESSAGES.WEEK_PLANNER_ADD_CANDIDATE}
          </button>
        </div>
      ))}
    </div>
  );
}

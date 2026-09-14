// The weekly summary screen (T39; design.md section 5, Screens table). Pure
// function of `useSummary`'s return shape - read-only, no promote/clear/add.

import { tokens } from '../tokens/index.js';
import { WeekLabel } from './WeekLabel.jsx';
import { RecipeDetailView } from './RecipeDetailView.jsx';
import { EmptyState } from './EmptyState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { DAY_LABELS, SLOT_LABELS } from '../domain/labels.js';
import { MESSAGES } from '../messages/index.js';

export function SummaryView({
  week,
  summary,
  isLoading,
  openDetail,
  detail,
  detailError,
  closeDetail,
  error,
}) {
  if (isLoading) return <LoadingState />;

  return (
    <div>
      {error ? <p style={{ color: tokens.color.ink, padding: tokens.space.md }}>{error}</p> : null}
      <h2 style={{ margin: tokens.space.none }}>{MESSAGES.SUMMARY_VIEW_TITLE}</h2>
      {week ? <WeekLabel designation="current" monday={week.monday} sunday={week.sunday} /> : null}
      {summary.isEmpty ? (
        <EmptyState message={MESSAGES.SUMMARY_VIEW_EMPTY} />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(7, minmax(0, 1fr))',
            gap: tokens.space.md,
            marginTop: tokens.space.md,
          }}
        >
          {summary.days.map((day) => (
            <div
              key={day.day}
              style={{ padding: tokens.space.sm, border: `1px solid ${tokens.color.line2}` }}
            >
              <p style={{ margin: tokens.space.none, color: tokens.color.ink }}>
                {DAY_LABELS[day.day]}
              </p>
              {day.slots.map((slotState) =>
                slotState.candidate ? (
                  <div key={slotState.slot} style={{ marginTop: tokens.space.sm }}>
                    <p style={{ margin: tokens.space.none, color: tokens.color.ink2 }}>
                      {SLOT_LABELS[slotState.slot]}
                    </p>
                    <button
                      type="button"
                      onClick={() => openDetail(slotState.candidate)}
                      style={{
                        color: tokens.color.terra,
                        backgroundColor: 'transparent',
                        border: 'none',
                        padding: tokens.space.none,
                      }}
                    >
                      {slotState.candidate.recipe.name}
                    </button>
                  </div>
                ) : null,
              )}
            </div>
          ))}
        </div>
      )}
      {detail || detailError ? (
        <RecipeDetailView recipe={detail} error={detailError} onClose={closeDetail} />
      ) : null}
    </div>
  );
}

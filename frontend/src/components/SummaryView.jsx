// The weekly summary screen (T39; design.md section 5, Screens table). Pure
// function of `useSummary`'s return shape - read-only, no promote/clear/add.

import { tokens } from '../tokens/index.js';
import { WeekLabel } from './WeekLabel.jsx';
import { RecipeDetailView } from './RecipeDetailView.jsx';
import { EmptyState } from './EmptyState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { DAY_LABELS, SLOT_LABELS } from '../domain/labels.js';
import { MESSAGES } from '../messages/index.js';
import { Banner } from './Banner.jsx';
import { VIEWPORT } from '../hooks/useViewport.js';
import { targetStyle } from '../tokens/controlStyles.js';

// Day-grid columns per viewport tier (frontend_ux_phase2 R22-R24).
function summaryColumns(viewport) {
  if (viewport === VIEWPORT.COMPACT) return '1fr';
  if (viewport === VIEWPORT.WIDE) return 'repeat(7, minmax(0, 1fr))';
  return `repeat(auto-fill, minmax(min(100%, ${tokens.layout.summaryDayMin}), 1fr))`;
}

const SLOT_LABEL_STYLE = {
  margin: tokens.space.none,
  fontFamily: tokens.fontFamily.label,
  fontSize: tokens.fontSize.xs,
  textTransform: 'uppercase',
  color: tokens.color.ink2,
};

// T89 (design.md 10.6): per-meal card shape + a "definitive" pill matching
// MealCard's (T82) treatment - every entry here already is the definitive
// meal, so the badge is unconditional rather than gated on `isDefinitive`.

export function SummaryView({
  week,
  summary,
  isLoading,
  openDetail,
  detail,
  detailError,
  closeDetail,
  error,
  viewport = VIEWPORT.WIDE,
}) {
  if (isLoading) return <LoadingState />;

  return (
    <div>
      <h2
        style={{
          margin: tokens.space.none,
          fontFamily: tokens.fontFamily.heading,
          fontSize: tokens.fontSize.xl,
        }}
      >
        {MESSAGES.SUMMARY_VIEW_TITLE}
      </h2>
      <Banner>{error}</Banner>
      {week ? <WeekLabel designation="current" monday={week.monday} sunday={week.sunday} /> : null}
      {summary.isEmpty ? (
        <EmptyState message={MESSAGES.SUMMARY_VIEW_EMPTY} />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: summaryColumns(viewport),
            gap: tokens.space.md,
            marginTop: tokens.space.md,
          }}
        >
          {summary.days.map((day) => (
            <div key={day.day} style={{ padding: tokens.space.sm }}>
              <p
                style={{
                  margin: tokens.space.none,
                  fontFamily: tokens.fontFamily.heading,
                  color: tokens.color.ink,
                }}
              >
                {DAY_LABELS[day.day]}
              </p>
              {day.slots.map((slotState) =>
                slotState.candidate ? (
                  <div
                    key={slotState.slot}
                    style={{
                      marginTop: tokens.space.sm,
                      padding: tokens.space.sm,
                      backgroundColor: tokens.color.surface,
                      border: `1px solid ${tokens.color.line}`,
                      borderRadius: tokens.radius.md,
                      boxShadow: tokens.shadow.sm,
                    }}
                  >
                    <p style={SLOT_LABEL_STYLE}>{SLOT_LABELS[slotState.slot]}</p>
                    <button
                      type="button"
                      onClick={() => openDetail(slotState.candidate)}
                      style={{
                        ...targetStyle(viewport),
                        color: tokens.color.terra,
                        backgroundColor: 'transparent',
                        border: 'none',
                        padding: tokens.space.none,
                        fontFamily: tokens.fontFamily.heading,
                        fontSize: tokens.fontSize.sm,
                      }}
                    >
                      {slotState.candidate.recipe.name}
                    </button>
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
                  </div>
                ) : (
                  <div key={slotState.slot} style={{ marginTop: tokens.space.sm }}>
                    <p style={SLOT_LABEL_STYLE}>{SLOT_LABELS[slotState.slot]}</p>
                    <p style={{ margin: tokens.space.none, color: tokens.color.ink3 }}>
                      {MESSAGES.SUMMARY_EMPTY_SLOT}
                    </p>
                  </div>
                ),
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

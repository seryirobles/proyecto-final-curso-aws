// The week planner screen (T15; design.md section 5, Screens table). Pure
// function of `useWeekPlanner`'s return shape - the App shell (a later
// section) is what wires `<WeekPlannerView {...useWeekPlanner()} />`.

// Day-card grid columns come from `weekGridColumns(viewport)` (frontend_ux_phase2 R26-R28).

import { tokens } from '../tokens/index.js';
import { WeekSwitcher } from './WeekSwitcher.jsx';
import { DaySlot } from './DaySlot.jsx';
import { RecipeDetailView } from './RecipeDetailView.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { LoadingState } from './LoadingState.jsx';
import { CandidateAuthoring } from './CandidateAuthoring.jsx';
import { Banner } from './Banner.jsx';
import { weekGridColumns } from '../tokens/controlStyles.js';
import { VIEWPORT } from '../hooks/useViewport.js';
import { useDayStrip } from '../hooks/useDayStrip.js';
import { DayStrip } from './DayStrip.jsx';

// Default for views rendered without a hook's `pending` set (R33).
const NO_PENDING = new Set();

export function WeekPlannerView({
  liveWeeks,
  designation,
  week,
  isLoading,
  switchWeek,
  openCandidateAuthoring,
  authoringTarget,
  submitCandidate,
  closeCandidateAuthoring,
  editingTarget,
  openCandidateEdit,
  closeCandidateEdit,
  submitCandidateEdit,
  removeCandidate,
  openDetail,
  promoteDefinitive,
  clearDefinitive,
  confirm,
  detail,
  detailError,
  closeDetail,
  error,
  pending = NO_PENDING,
  viewport = VIEWPORT.WIDE,
}) {
  const { registerDay, scrollToDay, selectedDay } = useDayStrip();
  if (isLoading) return <LoadingState />;
  const showStrip = viewport === VIEWPORT.COMPACT || viewport === VIEWPORT.NARROW;

  return (
    <div>
      {!authoringTarget && !editingTarget ? <Banner>{error}</Banner> : null}
      <WeekSwitcher
        liveWeeks={liveWeeks}
        designation={designation}
        onSwitch={switchWeek}
        viewport={viewport}
      />
      {showStrip ? <DayStrip selectedDay={selectedDay} onSelect={scrollToDay} /> : null}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: weekGridColumns(viewport),
          gap: tokens.space.md,
          marginTop: tokens.space.md,
        }}
      >
        {week.days.map((day) => (
          <DaySlot
            key={day.day}
            day={day.day}
            slots={day.slots}
            onAddCandidate={openCandidateAuthoring}
            onOpenDetail={openDetail}
            onPromote={promoteDefinitive}
            onClear={clearDefinitive}
            onEdit={openCandidateEdit}
            onRemove={removeCandidate}
            pending={pending}
            cardRef={registerDay(day.day)}
            viewport={viewport}
          />
        ))}
      </div>
      {authoringTarget || editingTarget ? <Banner>{error}</Banner> : null}
      {authoringTarget ? (
        <CandidateAuthoring
          onSubmit={submitCandidate}
          onClose={closeCandidateAuthoring}
          target={authoringTarget}
        />
      ) : null}
      {editingTarget ? (
        <CandidateAuthoring
          initialRecipe={editingTarget.recipe}
          target={editingTarget}
          onSubmit={submitCandidateEdit}
          onClose={closeCandidateEdit}
        />
      ) : null}
      <ConfirmDialog
        pending={confirm.pending}
        onConfirm={confirm.confirm}
        onCancel={confirm.cancel}
      />
      {detail || detailError ? (
        <RecipeDetailView recipe={detail} error={detailError} onClose={closeDetail} />
      ) : null}
    </div>
  );
}

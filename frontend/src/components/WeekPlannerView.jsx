// The week planner screen (T15; design.md section 5, Screens table). Pure
// function of `useWeekPlanner`'s return shape - the App shell (a later
// section) is what wires `<WeekPlannerView {...useWeekPlanner()} />`.

// Fluid day-card grid (T81, design.md 10.6): `auto-fill`/`minmax` so
// DaySlot's card shape collapses gracefully - no fixed breakpoint added.

import { tokens } from '../tokens/index.js';
import { WeekSwitcher } from './WeekSwitcher.jsx';
import { DaySlot } from './DaySlot.jsx';
import { RecipeDetailView } from './RecipeDetailView.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { LoadingState } from './LoadingState.jsx';
import { CandidateAuthoring } from './CandidateAuthoring.jsx';

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
}) {
  if (isLoading) return <LoadingState />;

  return (
    <div>
      {error ? (
        <p
          style={{
            color: tokens.color.honey,
            backgroundColor: tokens.color.honeySoft,
            borderRadius: tokens.radius.sm,
            padding: tokens.space.md,
          }}
        >
          {error}
        </p>
      ) : null}
      <WeekSwitcher liveWeeks={liveWeeks} designation={designation} onSwitch={switchWeek} />
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 260px), 1fr))',
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
          />
        ))}
      </div>
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

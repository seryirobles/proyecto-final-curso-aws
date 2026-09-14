// The week planner screen (T15; design.md section 5, Screens table). Pure
// function of `useWeekPlanner`'s return shape - the App shell (a later
// section) is what wires `<WeekPlannerView {...useWeekPlanner()} />`.

import { tokens } from '../tokens/index.js';
import { WeekSwitcher } from './WeekSwitcher.jsx';
import { DaySlot } from './DaySlot.jsx';
import { RecipeDetailView } from './RecipeDetailView.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { LoadingState } from './LoadingState.jsx';

export function WeekPlannerView({
  liveWeeks,
  designation,
  week,
  isLoading,
  switchWeek,
  openCandidateAuthoring,
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
      {error ? <p style={{ color: tokens.color.ink, padding: tokens.space.md }}>{error}</p> : null}
      <WeekSwitcher liveWeeks={liveWeeks} designation={designation} onSwitch={switchWeek} />
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(7, minmax(0, 1fr))',
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
          />
        ))}
      </div>
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

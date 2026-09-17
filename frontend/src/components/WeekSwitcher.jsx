// Switches the displayed live week between current/next (R2, R3; design.md
// section 5, section 10.6 - mined from the prototype's arrow-flanked week
// header). Pure - `liveWeeks` and `designation` come from `useWeekPlanner`.

import { tokens } from '../tokens/index.js';
import { formatDate } from '../locale.js';
import { MESSAGES } from '../messages/index.js';
import { WeekLabel } from './WeekLabel.jsx';

const ARROW_SIZE = '32px';

// FR-UX-06/G-57: names the target week's designation+range via `title`, so
// the non-displayed week's identity is never lost to WeekLabel showing only
// the active one (fix round, 2026-09-16).
function switchTitle(target, week) {
  const label = target === 'next' ? MESSAGES.WEEK_LABEL_NEXT : MESSAGES.WEEK_LABEL_CURRENT;
  return `${label} · ${formatDate(new Date(week.monday))}–${formatDate(new Date(week.sunday))}`;
}

// `isActive`: this arrow points at the week already displayed (a no-op
// click) - muted, so the one actionable arrow reads as inviting a click.
function arrowButtonStyle(isActive) {
  return {
    width: ARROW_SIZE,
    height: ARROW_SIZE,
    flex: 'none',
    borderRadius: tokens.radius.pill,
    border: `1px solid ${tokens.color.line}`,
    backgroundColor: tokens.color.surface,
    color: isActive ? tokens.color.ink3 : tokens.color.ink2,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };
}

export function WeekSwitcher({ liveWeeks, designation, onSwitch }) {
  if (!liveWeeks) return null;
  const active = liveWeeks[designation];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: tokens.space.sm }}>
      <button
        type="button"
        onClick={() => onSwitch('current')}
        title={switchTitle('current', liveWeeks.current)}
        style={arrowButtonStyle(designation === 'current')}
      >
        ‹
      </button>
      <WeekLabel designation={designation} monday={active.monday} sunday={active.sunday} />
      <button
        type="button"
        onClick={() => onSwitch('next')}
        title={switchTitle('next', liveWeeks.next)}
        style={arrowButtonStyle(designation === 'next')}
      >
        ›
      </button>
    </div>
  );
}

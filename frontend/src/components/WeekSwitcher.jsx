// Switches the displayed live week between current/next (R2, R3; design.md
// section 5). Pure - `liveWeeks` and `designation` come from `useWeekPlanner`.

import { tokens } from '../tokens/index.js';
import { WeekLabel } from './WeekLabel.jsx';

function switchButtonStyle(isActive) {
  return {
    padding: tokens.space.sm,
    backgroundColor: isActive ? tokens.color.terraSoft : tokens.color.surface,
    border: `1px solid ${tokens.color.line}`,
  };
}

export function WeekSwitcher({ liveWeeks, designation, onSwitch }) {
  if (!liveWeeks) return null;
  return (
    <div style={{ display: 'flex', gap: tokens.space.sm }}>
      <button
        type="button"
        onClick={() => onSwitch('current')}
        style={switchButtonStyle(designation === 'current')}
      >
        <WeekLabel
          designation="current"
          monday={liveWeeks.current.monday}
          sunday={liveWeeks.current.sunday}
        />
      </button>
      <button
        type="button"
        onClick={() => onSwitch('next')}
        style={switchButtonStyle(designation === 'next')}
      >
        <WeekLabel
          designation="next"
          monday={liveWeeks.next.monday}
          sunday={liveWeeks.next.sunday}
        />
      </button>
    </div>
  );
}

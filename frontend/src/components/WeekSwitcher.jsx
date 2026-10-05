// Switches the displayed live week between current/next as two segment
// buttons (frontend_ux_phase2 R37-R39). Pure - props come from `useWeekPlanner`.

import { tokens } from '../tokens/index.js';
import { WeekLabel } from './WeekLabel.jsx';
import { targetStyle } from '../tokens/controlStyles.js';
import { VIEWPORT } from '../hooks/useViewport.js';

function segmentStyle(isActive, viewport) {
  return {
    ...targetStyle(viewport),
    flex: 1,
    textAlign: 'left',
    border: `1px solid ${isActive ? tokens.color.terra : tokens.color.line}`,
    borderRadius: tokens.radius.sm,
    backgroundColor: isActive ? tokens.color.terraSoft : tokens.color.surface,
    padding: tokens.space.sm,
    fontWeight: isActive ? 700 : 400,
  };
}

export function WeekSwitcher({ liveWeeks, designation, onSwitch, viewport = VIEWPORT.WIDE }) {
  if (!liveWeeks) return null;

  return (
    <div style={{ display: 'flex', gap: tokens.space.sm }}>
      {['current', 'next'].map((target) => (
        <button
          key={target}
          type="button"
          onClick={() => onSwitch(target)}
          style={segmentStyle(designation === target, viewport)}
        >
          <WeekLabel
            designation={target}
            monday={liveWeeks[target].monday}
            sunday={liveWeeks[target].sunday}
          />
        </button>
      ))}
    </div>
  );
}

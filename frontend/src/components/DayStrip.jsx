// Sticky Monday-Sunday jump strip for compact/narrow viewports (frontend_ux_phase2 R29-R35, R57).

import { tokens } from '../tokens/index.js';
import { DAY_SHORT_LABELS } from '../domain/labels.js';

const DAYS = [1, 2, 3, 4, 5, 6, 7];

function dayButtonStyle(isSelected) {
  return {
    flex: 'none',
    minWidth: tokens.layout.targetMobile,
    minHeight: tokens.layout.targetMobile,
    border: `1px solid ${isSelected ? tokens.color.terra : tokens.color.line}`,
    borderRadius: tokens.radius.sm,
    backgroundColor: isSelected ? tokens.color.terraSoft : tokens.color.surface,
    color: tokens.color.ink,
    fontWeight: isSelected ? 700 : 400,
  };
}

export function DayStrip({ selectedDay, onSelect }) {
  return (
    <div
      style={{
        position: 'sticky',
        top: tokens.layout.headerHeight,
        height: tokens.layout.dayStripHeight,
        boxSizing: 'border-box',
        display: 'flex',
        flexWrap: 'nowrap',
        alignItems: 'center',
        gap: tokens.space.xs,
        padding: tokens.space.sm,
        overflowX: 'auto',
        backgroundColor: tokens.color.surface2,
      }}
    >
      {DAYS.map((day) => (
        <button
          key={day}
          type="button"
          onClick={() => onSelect(day)}
          style={dayButtonStyle(selectedDay === day)}
        >
          {DAY_SHORT_LABELS[day]}
        </button>
      ))}
    </div>
  );
}

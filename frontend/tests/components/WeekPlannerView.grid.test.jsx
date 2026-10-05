// @vitest-environment jsdom
// Week grid per viewport tier and compact empty slot (frontend_ux_phase2 R26-R28, R40).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { WeekPlannerView } from '../../src/components/WeekPlannerView.jsx';
import { weekGridColumns } from '../../src/tokens/controlStyles.js';
import { MESSAGES } from '../../src/messages/index.js';
import { DAY_LABELS } from '../../src/domain/labels.js';

afterEach(cleanup);

function props(viewport) {
  return {
    liveWeeks: {
      today: '2026-08-17',
      current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
      next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
    },
    designation: 'current',
    week: {
      weekId: '2026-W34',
      days: Array.from({ length: 7 }, (_, i) => ({
        day: i + 1,
        slots: [
          { slot: 1, candidates: [], definitiveId: null, isEmpty: true },
          { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
        ],
      })),
    },
    isLoading: false,
    switchWeek: vi.fn(),
    openCandidateAuthoring: vi.fn(),
    openDetail: vi.fn(),
    promoteDefinitive: vi.fn(),
    clearDefinitive: vi.fn(),
    confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
    detail: null,
    closeDetail: vi.fn(),
    viewport,
  };
}

function gridAt(viewport) {
  render(<WeekPlannerView {...props(viewport)} />);
  return screen.getByText(DAY_LABELS[1]).parentElement.parentElement.parentElement;
}

describe('week grid', () => {
  it('has seven equal columns when wide (R26)', () => {
    const grid = gridAt('wide');
    expect(grid.style.gridTemplateColumns).toBe('repeat(7, minmax(0, 1fr))');
    expect(grid.children).toHaveLength(7);
  });

  it('has four columns when medium, wrapping 4 + 3 (R27)', () => {
    expect(gridAt('medium').style.gridTemplateColumns).toBe('repeat(4, minmax(0, 1fr))');
  });

  it.each(['compact', 'narrow'])('has a single column when %s (R28)', (vp) => {
    expect(gridAt(vp).style.gridTemplateColumns).toBe('minmax(0, 1fr)');
  });

  it('maps tiers through weekGridColumns', () => {
    expect(weekGridColumns('wide')).toBe('repeat(7, minmax(0, 1fr))');
    expect(weekGridColumns('medium')).toBe('repeat(4, minmax(0, 1fr))');
    expect(weekGridColumns('narrow')).toBe('minmax(0, 1fr)');
  });
});

describe('empty slot', () => {
  it('renders the message as a plain paragraph without the dashed box (R40)', () => {
    render(<WeekPlannerView {...props('wide')} />);
    const message = screen.getAllByText(MESSAGES.WEEK_PLANNER_EMPTY_SLOT)[0];
    expect(message.tagName).toBe('P');
    expect(message.style.border).toBe('');
    expect(message.style.textAlign).not.toBe('center');
  });
});

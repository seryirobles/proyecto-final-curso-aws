// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { DaySlot } from '../../src/components/DaySlot.jsx';
import { MESSAGES } from '../../src/messages/index.js';

// `vite.config.js` sets `globals: false`, so @testing-library/react's
// auto-cleanup never registers - see WeekPlannerView.test.jsx.
afterEach(cleanup);

function candidate(id, name) {
  return {
    id,
    author: 'Marta',
    recipe: {
      name,
      category: 'legume',
      servings: 4,
      estimatedTime: '45 min',
      ingredients: [],
      tools: [],
      procedure: [],
    },
  };
}

function emptySlots() {
  return [
    { slot: 1, candidates: [], definitiveId: null, isEmpty: true },
    { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
  ];
}

function baseProps(overrides = {}) {
  return {
    day: 3,
    slots: emptySlots(),
    onAddCandidate: vi.fn(),
    onOpenDetail: vi.fn(),
    onPromote: vi.fn(),
    onClear: vi.fn(),
    ...overrides,
  };
}

describe('DaySlot', () => {
  it('shows the empty status when no slot has a candidate (dayStatus, empty branch)', () => {
    render(<DaySlot {...baseProps()} />);

    expect(screen.getByText(MESSAGES.WEEK_PLANNER_DAY_STATUS_EMPTY)).not.toBeNull();
  });

  it('shows the candidates status when a slot has candidates but no definitive meal (dayStatus, candidates branch)', () => {
    const slots = [
      { slot: 1, candidates: [candidate('c1', 'Lentejas')], definitiveId: null, isEmpty: false },
      { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
    ];

    render(<DaySlot {...baseProps({ slots })} />);

    expect(screen.getByText(MESSAGES.WEEK_PLANNER_DAY_STATUS_CANDIDATES)).not.toBeNull();
  });

  it('shows the definitive status when a slot has a definitive meal (dayStatus, definitive branch)', () => {
    const slots = [
      { slot: 1, candidates: [candidate('c1', 'Lentejas')], definitiveId: 'c1', isEmpty: false },
      { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
    ];

    render(<DaySlot {...baseProps({ slots })} />);

    expect(screen.getByText(MESSAGES.WEEK_PLANNER_DAY_STATUS_DEFINITIVE)).not.toBeNull();
  });

  it('prefers the definitive status over a pending-candidates status in another slot (dayStatus precedence)', () => {
    const slots = [
      { slot: 1, candidates: [candidate('c1', 'Tortilla')], definitiveId: 'c1', isEmpty: false },
      { slot: 2, candidates: [candidate('c2', 'Ensalada')], definitiveId: null, isEmpty: false },
    ];

    render(<DaySlot {...baseProps({ slots })} />);

    expect(screen.getByText(MESSAGES.WEEK_PLANNER_DAY_STATUS_DEFINITIVE)).not.toBeNull();
    expect(screen.queryByText(MESSAGES.WEEK_PLANNER_DAY_STATUS_CANDIDATES)).toBeNull();
  });

  it('clicking the promote control calls onPromote with (day, slot, candidateId)', () => {
    const slots = [
      { slot: 1, candidates: [candidate('c1', 'Lentejas')], definitiveId: null, isEmpty: false },
      { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
    ];
    const onPromote = vi.fn();

    render(<DaySlot {...baseProps({ day: 3, slots, onPromote })} />);
    fireEvent.click(screen.getByText(MESSAGES.WEEK_PLANNER_PROMOTE_DEFINITIVE));

    expect(onPromote).toHaveBeenCalledWith(3, 1, 'c1');
  });
});

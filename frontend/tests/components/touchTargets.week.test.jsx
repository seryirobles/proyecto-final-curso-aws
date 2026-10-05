// @vitest-environment jsdom
// Touch targets in the week views (frontend_ux_phase2 R41, R43).
import { afterEach, describe, it, vi } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import { WeekPlannerView } from '../../src/components/WeekPlannerView.jsx';
import { WeekSwitcher } from '../../src/components/WeekSwitcher.jsx';
import { MealCard } from '../../src/components/MealCard.jsx';
import { DaySlot } from '../../src/components/DaySlot.jsx';
import { expectTargets } from '../helpers/targets.js';

afterEach(cleanup);

const CANDIDATE = { id: 'c1', author: 'Ana', recipe: { name: 'Lentejas' } };
const LIVE_WEEKS = {
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};
const noop = vi.fn();

function card(viewport, isDefinitive) {
  return render(
    <MealCard
      candidate={CANDIDATE}
      isDefinitive={isDefinitive}
      onOpenDetail={noop}
      onPromote={noop}
      onClear={noop}
      onEdit={noop}
      onRemove={noop}
      viewport={viewport}
    />,
  );
}

function slot(viewport) {
  const slots = [
    { slot: 1, candidates: [CANDIDATE], definitiveId: null, isEmpty: false },
    { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
  ];
  return render(
    <DaySlot
      day={1}
      slots={slots}
      onAddCandidate={noop}
      onOpenDetail={noop}
      onPromote={noop}
      onClear={noop}
      onEdit={noop}
      onRemove={noop}
      viewport={viewport}
    />,
  );
}

describe.each([
  ['compact', '44px'],
  ['narrow', '44px'],
  ['medium', '24px'],
  ['wide', '24px'],
])('week buttons when %s', (viewport, px) => {
  it('MealCard (candidate and definitive)', () => {
    expectTargets(card(viewport, false).container, px, 4);
    cleanup();
    expectTargets(card(viewport, true).container, px, 4);
  });

  it('DaySlot add buttons', () => {
    expectTargets(slot(viewport).container, px, 6);
  });

  it('WeekSwitcher', () => {
    const { container } = render(
      <WeekSwitcher
        liveWeeks={LIVE_WEEKS}
        designation="current"
        onSwitch={noop}
        viewport={viewport}
      />,
    );
    expectTargets(container, px, 2);
  });

  it('WeekPlannerView passes the viewport down to every button', () => {
    const week = {
      weekId: '2026-W34',
      days: [
        {
          day: 1,
          slots: [{ slot: 1, candidates: [CANDIDATE], definitiveId: null, isEmpty: false }],
        },
      ],
    };
    const { container } = render(
      <WeekPlannerView
        liveWeeks={LIVE_WEEKS}
        designation="current"
        week={week}
        isLoading={false}
        confirm={{ pending: null, confirm: noop, cancel: noop }}
        viewport={viewport}
      />,
    );
    const strip = viewport === 'compact' || viewport === 'narrow' ? 7 : 0;
    expectTargets(container, px, 2 + strip + 4 + 1);
  });
});

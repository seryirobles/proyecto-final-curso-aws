// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { WeekSwitcher } from '../../src/components/WeekSwitcher.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { formatDate } from '../../src/locale.js';

afterEach(cleanup);

const LIVE_WEEKS = {
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function arrows() {
  const buttons = screen.getAllByRole('button');
  return { back: buttons[0], forward: buttons[1] };
}

describe('WeekSwitcher', () => {
  it('the back arrow calls onSwitch with "current" and the forward arrow calls onSwitch with "next" (distinct assertions)', () => {
    const onSwitch = vi.fn();
    render(<WeekSwitcher liveWeeks={LIVE_WEEKS} designation="current" onSwitch={onSwitch} />);
    const { back, forward } = arrows();

    fireEvent.click(back);
    expect(onSwitch).toHaveBeenCalledWith('current');

    fireEvent.click(forward);
    expect(onSwitch).toHaveBeenCalledWith('next');
  });

  it('renders the next week\'s WeekLabel (designation + own range), not the current week\'s, when designation is "next"', () => {
    render(<WeekSwitcher liveWeeks={LIVE_WEEKS} designation="next" onSwitch={vi.fn()} />);

    const nextRange = `${formatDate(new Date(LIVE_WEEKS.next.monday))}–${formatDate(new Date(LIVE_WEEKS.next.sunday))}`;
    const currentRange = `${formatDate(new Date(LIVE_WEEKS.current.monday))}–${formatDate(new Date(LIVE_WEEKS.current.sunday))}`;

    expect(screen.getByText(MESSAGES.WEEK_LABEL_NEXT)).not.toBeNull();
    expect(screen.getByText(nextRange)).not.toBeNull();
    expect(screen.queryByText(MESSAGES.WEEK_LABEL_CURRENT)).toBeNull();
    expect(screen.queryByText(currentRange)).toBeNull();
  });

  it('titles each arrow with the week it switches to, designation and range (FR-UX-06/G-57)', () => {
    render(<WeekSwitcher liveWeeks={LIVE_WEEKS} designation="current" onSwitch={vi.fn()} />);
    const { back, forward } = arrows();

    const currentRange = `${formatDate(new Date(LIVE_WEEKS.current.monday))}–${formatDate(new Date(LIVE_WEEKS.current.sunday))}`;
    const nextRange = `${formatDate(new Date(LIVE_WEEKS.next.monday))}–${formatDate(new Date(LIVE_WEEKS.next.sunday))}`;

    expect(back.title).toBe(`${MESSAGES.WEEK_LABEL_CURRENT} · ${currentRange}`);
    expect(forward.title).toBe(`${MESSAGES.WEEK_LABEL_NEXT} · ${nextRange}`);
  });
});

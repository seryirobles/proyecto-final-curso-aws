// @vitest-environment jsdom
// Week switcher as two segment buttons (frontend_ux_phase2 R37-R39).
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

const range = (w) => `${formatDate(new Date(w.monday))}–${formatDate(new Date(w.sunday))}`;

describe('WeekSwitcher', () => {
  it('renders two buttons, each with designation and range (R37)', () => {
    render(<WeekSwitcher liveWeeks={LIVE_WEEKS} designation="current" onSwitch={vi.fn()} />);
    const [current, next] = screen.getAllByRole('button');
    expect(screen.getAllByRole('button')).toHaveLength(2);
    expect(current.textContent).toContain(MESSAGES.WEEK_LABEL_CURRENT);
    expect(current.textContent).toContain(range(LIVE_WEEKS.current));
    expect(next.textContent).toContain(MESSAGES.WEEK_LABEL_NEXT);
    expect(next.textContent).toContain(range(LIVE_WEEKS.next));
  });

  it('highlights only the displayed week with bold and a terra border (R38)', () => {
    render(<WeekSwitcher liveWeeks={LIVE_WEEKS} designation="next" onSwitch={vi.fn()} />);
    const [current, next] = screen.getAllByRole('button');
    expect(next.style.fontWeight).toBe('700');
    expect(current.style.fontWeight).not.toBe('700');
    expect(next.style.border).not.toBe(current.style.border);
  });

  it('calls onSwitch with the button designation (R39)', () => {
    const onSwitch = vi.fn();
    render(<WeekSwitcher liveWeeks={LIVE_WEEKS} designation="current" onSwitch={onSwitch} />);
    const [current, next] = screen.getAllByRole('button');
    fireEvent.click(next);
    expect(onSwitch).toHaveBeenLastCalledWith('next');
    fireEvent.click(current);
    expect(onSwitch).toHaveBeenLastCalledWith('current');
  });

  it('renders nothing without liveWeeks', () => {
    const { container } = render(
      <WeekSwitcher liveWeeks={null} designation="current" onSwitch={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
  });
});

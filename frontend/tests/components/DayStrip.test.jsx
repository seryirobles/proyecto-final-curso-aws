// @vitest-environment jsdom
// Day strip (frontend_ux_phase2 R29-R36, R57) and its WeekPlannerView wiring.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { WeekPlannerView } from '../../src/components/WeekPlannerView.jsx';
import { DayStrip } from '../../src/components/DayStrip.jsx';
import { DAY_LABELS } from '../../src/domain/labels.js';
import { tokens } from '../../src/tokens/index.js';

afterEach(cleanup);

const SHORT = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

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

function stripButtons() {
  return SHORT.map((label) => screen.queryByRole('button', { name: label }));
}

beforeEach(() => {
  window.Element.prototype.scrollIntoView = vi.fn();
});

describe('DayStrip', () => {
  it.each(['compact', 'narrow'])('is rendered when %s (R29)', (viewport) => {
    render(<WeekPlannerView {...props(viewport)} />);
    expect(stripButtons().every((b) => b !== null)).toBe(true);
  });

  it.each(['medium', 'wide'])('is not rendered when %s (R30)', (viewport) => {
    render(<WeekPlannerView {...props(viewport)} />);
    expect(stripButtons().every((b) => b === null)).toBe(true);
  });

  it('has seven buttons in order with visible labels and no aria-label (R31)', () => {
    render(<DayStrip selectedDay={null} onSelect={vi.fn()} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons.map((b) => b.textContent)).toEqual(SHORT);
    buttons.forEach((b) => expect(b.hasAttribute('aria-label')).toBe(false));
  });

  it('does not shrink or wrap and scrolls horizontally (R32, R57)', () => {
    render(<DayStrip selectedDay={null} onSelect={vi.fn()} />);
    const first = screen.getByRole('button', { name: 'Lun' });
    expect(first.style.minWidth).toBe(tokens.layout.targetMobile);
    expect(first.style.flexShrink).toBe('0');
    const strip = first.parentElement;
    expect(strip.style.overflowX).toBe('auto');
    expect(strip.style.flexWrap).toBe('nowrap');
  });

  it('is sticky below the header (R35)', () => {
    render(<DayStrip selectedDay={null} onSelect={vi.fn()} />);
    const strip = screen.getByRole('button', { name: 'Lun' }).parentElement;
    expect(strip.style.position).toBe('sticky');
    expect(strip.style.top).toBe(tokens.layout.headerHeight);
    expect(strip.style.height).toBe(tokens.layout.dayStripHeight);
  });

  it('tapping a day scrolls its card into view and selects it (R33, R34)', () => {
    render(<WeekPlannerView {...props('compact')} />);
    fireEvent.click(screen.getByRole('button', { name: 'Mié' }));
    const card = screen.getByText(DAY_LABELS[3]).parentElement.parentElement;
    expect(window.Element.prototype.scrollIntoView).toHaveBeenCalledTimes(1);
    expect(window.Element.prototype.scrollIntoView.mock.contexts[0]).toBe(card);
    const selected = screen.getByRole('button', { name: 'Mié' });
    expect(selected.style.fontWeight).toBe('700');
    const probe = document.createElement('div');
    probe.style.borderColor = tokens.color.terra;
    expect(selected.style.borderColor).toBe(probe.style.borderColor);
    expect(screen.getByRole('button', { name: 'Mar' }).style.borderColor).not.toBe(
      probe.style.borderColor,
    );
    expect(screen.getByRole('button', { name: 'Mar' }).style.fontWeight).not.toBe('700');
  });

  it('gives each day card a scroll margin of header plus strip height (R36)', () => {
    render(<WeekPlannerView {...props('compact')} />);
    const card = screen.getByText(DAY_LABELS[1]).parentElement.parentElement;
    // jsdom folds the calc: 56px + 48px.
    expect(card.style.scrollMarginTop).toBe('calc(104px)');
  });
});

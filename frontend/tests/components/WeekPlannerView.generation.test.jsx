// @vitest-environment jsdom
// Feature 35 (T8): the entry point, empty week and panel guard in the week view.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { WeekPlannerView } from '../../src/components/WeekPlannerView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function days(filled = false) {
  return Array.from({ length: 7 }, (_, i) => ({
    day: i + 1,
    slots: [1, 2].map((slot) => ({
      slot,
      candidates:
        filled && i === 0 && slot === 1
          ? [{ id: 'c', author: 'Ana', recipe: { name: 'Sopa' } }]
          : [],
      definitiveId: null,
      isEmpty: !(filled && i === 0 && slot === 1),
    })),
  }));
}

function generation(overrides = {}) {
  return {
    phase: 'closed',
    isOpen: false,
    isBusy: false,
    runWeekId: null,
    panelKey: null,
    open: vi.fn(),
    mode: 'mix',
    setMode: vi.fn(),
    rules: [],
    rulesLoading: false,
    availableOptions: null,
    overrideDraft: null,
    startOverride: vi.fn(),
    setCategoryCount: vi.fn(),
    setDisabledDays: vi.fn(),
    submit: vi.fn(),
    close: vi.fn(),
    dismiss: vi.fn(),
    retrySlot: vi.fn(),
    pending: new Set(),
    slots: [],
    progress: { done: 0, total: 0 },
    skippedPins: [],
    error: null,
    ...overrides,
  };
}

function props(overrides = {}) {
  return {
    liveWeeks: LIVE_WEEKS,
    designation: 'current',
    week: { weekId: '2026-W34', days: days(true) },
    isLoading: false,
    switchWeek: vi.fn(),
    confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
    generation: generation(),
    ...overrides,
  };
}

describe('WeekPlannerView generation entry point', () => {
  it('shows the button directly below the week switcher (R1)', () => {
    render(<WeekPlannerView {...props()} />);
    const button = screen.getByText(MESSAGES.WEEK_GEN_BUTTON);
    const switcherLast = screen.getByText(MESSAGES.WEEK_LABEL_NEXT).closest('button');
    expect(switcherLast.parentElement.nextElementSibling).toBe(button);
  });

  it('opens the panel on activation (R3)', () => {
    const open = vi.fn();
    render(<WeekPlannerView {...props({ generation: generation({ open }) })} />);
    fireEvent.click(screen.getByText(MESSAGES.WEEK_GEN_BUTTON));
    expect(open).toHaveBeenCalled();
  });

  it('disables the button while a run is submitting or in progress (R4)', () => {
    render(<WeekPlannerView {...props({ generation: generation({ isBusy: true }) })} />);
    expect(screen.getByText(MESSAGES.WEEK_GEN_BUTTON).disabled).toBe(true);
  });

  it('shows the empty-state only when every slot is empty (R2)', () => {
    render(<WeekPlannerView {...props({ week: { weekId: '2026-W34', days: days(false) } })} />);
    expect(screen.getByText(MESSAGES.WEEK_GEN_EMPTY_WEEK)).not.toBeNull();
    cleanup();
    render(<WeekPlannerView {...props()} />);
    expect(screen.queryByText(MESSAGES.WEEK_GEN_EMPTY_WEEK)).toBeNull();
  });

  it('renders the panel only for the displayed week (R43)', () => {
    const open = generation({ isOpen: true, phase: 'configuring', runWeekId: '2026-W34' });
    render(<WeekPlannerView {...props({ generation: open })} />);
    expect(screen.getByText(MESSAGES.WEEK_GEN_PANEL_TITLE)).not.toBeNull();
    cleanup();
    render(<WeekPlannerView {...props({ generation: { ...open, runWeekId: '2026-W35' } })} />);
    expect(screen.queryByText(MESSAGES.WEEK_GEN_PANEL_TITLE)).toBeNull();
  });

  it('passes the viewport to the button target size (R49)', () => {
    render(<WeekPlannerView {...props()} viewport="compact" />);
    const button = screen.getByText(MESSAGES.WEEK_GEN_BUTTON);
    expect([button.style.minHeight, button.style.minWidth]).toEqual(['44px', '44px']);
  });

  it('shows no button when the hook state is absent', () => {
    render(<WeekPlannerView {...props({ generation: undefined })} />);
    expect(screen.queryByText(MESSAGES.WEEK_GEN_BUTTON)).toBeNull();
  });
});

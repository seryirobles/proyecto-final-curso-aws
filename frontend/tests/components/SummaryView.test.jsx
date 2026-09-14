// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within, fireEvent, cleanup } from '@testing-library/react';
import { SummaryView } from '../../src/components/SummaryView.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { DAY_LABELS, SLOT_LABELS } from '../../src/domain/labels.js';

afterEach(cleanup);

function emptyDays() {
  return Array.from({ length: 7 }, (_, i) => ({
    day: i + 1,
    slots: [
      { day: i + 1, slot: 1, candidate: null },
      { day: i + 1, slot: 2, candidate: null },
    ],
  }));
}

function candidate() {
  return {
    id: 'c1',
    author: 'Marta',
    recipe: {
      name: 'Lentejas al curry',
      category: 'legume',
      servings: 4,
      estimatedTime: '45 min',
      ingredients: [],
      tools: [],
      procedure: [],
    },
  };
}

function baseProps(overrides = {}) {
  return {
    week: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
    summary: { weekId: '2026-W34', days: emptyDays(), isEmpty: true },
    isLoading: false,
    openDetail: vi.fn(),
    detail: null,
    closeDetail: vi.fn(),
    ...overrides,
  };
}

describe('SummaryView', () => {
  it('renders LoadingState during the initial fetch instead of the grid', () => {
    render(<SummaryView {...baseProps({ isLoading: true })} />);

    expect(screen.getByText(MESSAGES.LOADING_STATE_DEFAULT)).not.toBeNull();
    expect(screen.queryByText(MESSAGES.SUMMARY_VIEW_TITLE)).toBeNull();
  });

  it('renders the WeekLabel header with the current designation and range (R21)', () => {
    render(<SummaryView {...baseProps()} />);

    expect(screen.getByText(/Semana actual/)).not.toBeNull();
  });

  it('zero definitives sets the empty-state flag (R19)', () => {
    render(<SummaryView {...baseProps()} />);

    expect(screen.getByText(MESSAGES.SUMMARY_VIEW_EMPTY)).not.toBeNull();
  });

  it('clicking a meal calls openDetail with that candidate, same opener pattern as T21 (R5)', () => {
    const meal = candidate();
    const days = emptyDays();
    days[2].slots[1] = { day: 3, slot: 2, candidate: meal };
    const openDetail = vi.fn();

    render(
      <SummaryView
        {...baseProps({ summary: { weekId: '2026-W34', days, isEmpty: false }, openDetail })}
      />,
    );
    fireEvent.click(screen.getByText('Lentejas al curry'));

    expect(openDetail).toHaveBeenCalledWith(meal);
  });

  it('renders only the slot holding the definitive, not every slot of that day', () => {
    const meal = candidate();
    const days = emptyDays();
    days[2].slots[1] = { day: 3, slot: 2, candidate: meal };

    render(
      <SummaryView {...baseProps({ summary: { weekId: '2026-W34', days, isEmpty: false } })} />,
    );

    expect(screen.getAllByText('Lentejas al curry')).toHaveLength(1);
    expect(screen.queryByText(MESSAGES.SUMMARY_VIEW_EMPTY)).toBeNull();
  });

  it('renders the meal under its own day column, labeled with its own slot (day/slot mapping)', () => {
    const meal = candidate();
    const days = emptyDays();
    days[2].slots[1] = { day: 3, slot: 2, candidate: meal };

    render(
      <SummaryView {...baseProps({ summary: { weekId: '2026-W34', days, isEmpty: false } })} />,
    );

    const wednesdayColumn = screen.getByText(DAY_LABELS[3]).closest('div');
    expect(within(wednesdayColumn).getByText('Lentejas al curry')).not.toBeNull();
    expect(within(wednesdayColumn).getByText(SLOT_LABELS[2])).not.toBeNull();

    const tuesdayColumn = screen.getByText(DAY_LABELS[2]).closest('div');
    expect(within(tuesdayColumn).queryByText('Lentejas al curry')).toBeNull();
  });

  it('renders RecipeDetailView when detail is set, closing it via closeDetail', () => {
    const recipe = {
      name: 'Tortilla',
      category: 'eggs',
      servings: 2,
      estimatedTime: '20 min',
      ingredients: [],
      tools: [],
      procedure: [],
    };
    const closeDetail = vi.fn();

    render(<SummaryView {...baseProps({ detail: recipe, closeDetail })} />);
    expect(screen.getByText('Tortilla')).not.toBeNull();

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_DETAIL_CLOSE));
    expect(closeDetail).toHaveBeenCalledTimes(1);
  });

  it('renders the fetch error detail when present (R15)', () => {
    render(<SummaryView {...baseProps({ error: 'No se pudo cargar.' })} />);

    expect(screen.getByText('No se pudo cargar.')).not.toBeNull();
  });
});

// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { WeekPlannerView } from '../../src/components/WeekPlannerView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

// `vite.config.js` sets `globals: false`, so @testing-library/react's
// auto-cleanup (which hooks a global `afterEach`) never registers - every
// render() here must be torn down explicitly between tests.
afterEach(cleanup);

function emptyDays() {
  return Array.from({ length: 7 }, (_, i) => ({
    day: i + 1,
    slots: [
      { slot: 1, candidates: [], definitiveId: null, isEmpty: true },
      { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
    ],
  }));
}

function baseProps(overrides = {}) {
  return {
    liveWeeks: {
      today: '2026-08-17',
      current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
      next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
    },
    designation: 'current',
    week: { weekId: '2026-W34', days: emptyDays() },
    isLoading: false,
    switchWeek: vi.fn(),
    openCandidateAuthoring: vi.fn(),
    openDetail: vi.fn(),
    promoteDefinitive: vi.fn(),
    clearDefinitive: vi.fn(),
    confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
    detail: null,
    closeDetail: vi.fn(),
    ...overrides,
  };
}

describe('WeekPlannerView', () => {
  it('renders seven days x two slots for a given week payload (R1)', () => {
    render(<WeekPlannerView {...baseProps()} />);

    expect(screen.getAllByText(MESSAGES.WEEK_PLANNER_EMPTY_SLOT)).toHaveLength(14);
    expect(screen.getAllByText(MESSAGES.WEEK_PLANNER_ADD_CANDIDATE)).toHaveLength(14);
  });

  it('renders the same component tree shape for a current and a next fixture (R3)', () => {
    const { container: currentContainer } = render(<WeekPlannerView {...baseProps()} />);
    const currentButtonCount = currentContainer.querySelectorAll('button').length;
    cleanup();
    const nextProps = baseProps({
      designation: 'next',
      week: { weekId: '2026-W35', days: emptyDays() },
    });
    const { container: nextContainer } = render(<WeekPlannerView {...nextProps} />);

    expect(nextContainer.querySelectorAll('button').length).toBe(currentButtonCount);
  });

  it('renders LoadingState during the initial fetch instead of the grid', () => {
    render(<WeekPlannerView {...baseProps({ isLoading: true })} />);

    expect(screen.getByText(MESSAGES.LOADING_STATE_DEFAULT)).not.toBeNull();
    expect(screen.queryByText(MESSAGES.WEEK_PLANNER_ADD_CANDIDATE)).toBeNull();
  });

  it('clicking a meal card calls openDetail with that candidate', () => {
    const candidate = {
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
    const days = emptyDays();
    days[0].slots[1] = { slot: 2, candidates: [candidate], definitiveId: 'c1', isEmpty: false };
    const openDetail = vi.fn();

    render(<WeekPlannerView {...baseProps({ week: { weekId: '2026-W34', days }, openDetail })} />);
    fireEvent.click(screen.getByText('Lentejas al curry'));

    expect(openDetail).toHaveBeenCalledWith(candidate);
  });

  it('renders the definitive meal card with a clear control instead of a promote control', () => {
    const candidate = {
      id: 'c1',
      author: 'Marta',
      recipe: {
        name: 'Lentejas',
        category: 'legume',
        servings: 4,
        estimatedTime: '45 min',
        ingredients: [],
        tools: [],
        procedure: [],
      },
    };
    const days = emptyDays();
    days[0].slots[1] = { slot: 2, candidates: [candidate], definitiveId: 'c1', isEmpty: false };
    const clearDefinitive = vi.fn();

    render(
      <WeekPlannerView {...baseProps({ week: { weekId: '2026-W34', days }, clearDefinitive })} />,
    );
    fireEvent.click(screen.getByText(MESSAGES.WEEK_PLANNER_CLEAR_DEFINITIVE));

    expect(clearDefinitive).toHaveBeenCalledWith(1, 2);
    expect(screen.queryByText(MESSAGES.WEEK_PLANNER_PROMOTE_DEFINITIVE)).toBeNull();
  });

  it('renders the mutation error detail when present (R15)', () => {
    render(<WeekPlannerView {...baseProps({ error: 'No se pudo guardar.' })} />);

    expect(screen.getByText('No se pudo guardar.')).not.toBeNull();
  });

  it('renders RecipeDetailView for a detail fetch error even without a recipe (R15)', () => {
    render(<WeekPlannerView {...baseProps({ detailError: 'No existe la receta.' })} />);

    expect(screen.getByText('No existe la receta.')).not.toBeNull();
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

    render(<WeekPlannerView {...baseProps({ detail: recipe, closeDetail })} />);
    expect(screen.getByText('Tortilla')).not.toBeNull();

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_DETAIL_CLOSE));
    expect(closeDetail).toHaveBeenCalledTimes(1);
  });
});

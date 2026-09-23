// @vitest-environment jsdom
// Issue add-dish-button-inert, scope extension of 2026-09-22 (E5-E10): a meal
// in the week view must also be editable (PUT) and removable (DELETE), the
// other two thirds of FR-CAND-01. Same root cause as the add path, same
// harness: the real useWeekPlanner + WeekPlannerView pair, usePolling and
// apiFetch mocked.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch, ApiError } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useWeekPlanner } from '../../src/hooks/useWeekPlanner.js';
import { WeekPlannerView } from '../../src/components/WeekPlannerView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

// The copy this flow needs, stated here so the interaction assertions below
// fail on the missing control, not on an undefined MESSAGES key.
const EDIT = 'Editar';
const REMOVE = 'Eliminar';
const CONFIRM_REMOVE = '¿Eliminar este plato de este hueco?';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

const CANDIDATE = {
  id: 'c1',
  author: 'Marta',
  recipe: {
    name: 'Lentejas al curry',
    category: 'legume',
    servings: 4,
    estimatedTime: '45 min',
    // Non-empty sections (issue recipe-saved-without-required-sections, G-89,
    // landed after this fixture was approved): required for the seeded edit
    // form's submit button to be enabled at all; no assertion touched.
    ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
    tools: ['olla'],
    procedure: ['Cocer las lentejas.'],
  },
};

// One candidate, in day 1 / slot 2, so every control below is unique.
const WEEK = {
  weekId: '2026-W34',
  slots: [{ day: 1, slot: 2, candidates: [CANDIDATE], definitiveId: null }],
};

// Same slot, promoted to definitive - review finding (fix round 1): E5-E10
// claim Editar/Eliminar render for a definitive meal too (FR-CAND-05), but
// no fixture before this one ever set definitiveId, so a mutant gating both
// buttons behind `!isDefinitive` survived the whole suite undetected.
const DEFINITIVE_WEEK = {
  weekId: '2026-W34',
  slots: [{ day: 1, slot: 2, candidates: [CANDIDATE], definitiveId: 'c1' }],
};

const CANDIDATE_URL = '/v1/weeks/2026-W34/days/1/slots/2/candidates/c1';

function Wrapper() {
  const planner = useWeekPlanner();
  return <WeekPlannerView {...planner} />;
}

function mockPolls(week = WEEK) {
  const applyMutationMarker = vi.fn();
  usePolling.mockImplementation((url) => ({
    data: url === '/v1/library/recipes' ? { recipes: [] } : week,
    marker: 1,
    connectionLost: false,
    applyMutationMarker,
    refetchNow: vi.fn(), // issue ui-not-reflecting-mutations
  }));
  return applyMutationMarker;
}

function mockApi({ onMutate } = {}) {
  apiFetch.mockImplementation((url, options) => {
    if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
    if (onMutate) return onMutate(url, options);
    options?.onHeaders?.(new Headers({ ETag: '"21"' }));
    return Promise.resolve({ candidate: CANDIDATE });
  });
}

async function openEdit() {
  const button = await screen.findByText(EDIT);
  fireEvent.click(button);
}

async function clickRemove() {
  const button = await screen.findByText(REMOVE);
  fireEvent.click(button);
}

function mutationCalls() {
  return apiFetch.mock.calls.filter(([url]) => url === CANDIDATE_URL);
}

describe('WeekPlannerView candidate edit and remove', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it('exposes the week-view edit and remove copy through MESSAGES (E5, E7, FR-UX-01)', () => {
    expect(MESSAGES.WEEK_PLANNER_EDIT_CANDIDATE).toBe(EDIT);
    expect(MESSAGES.WEEK_PLANNER_REMOVE_CANDIDATE).toBe(REMOVE);
    expect(MESSAGES.CONFIRM_REMOVE_CANDIDATE).toBe(CONFIRM_REMOVE);
  });

  it('renders Editar and Eliminar for a definitive meal too, both functional (E6, FR-CAND-05)', async () => {
    mockPolls(DEFINITIVE_WEEK);
    mockApi();
    render(<Wrapper />);

    expect(await screen.findByText(EDIT)).not.toBeNull();
    expect(screen.getByText(REMOVE)).not.toBeNull();

    await openEdit();
    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        CANDIDATE_URL,
        expect.objectContaining({ method: 'PUT' }),
      ),
    );

    await clickRemove();
    fireEvent.click(screen.getByText(MESSAGES.CONFIRM_DIALOG_CONFIRM));
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        CANDIDATE_URL,
        expect.objectContaining({ method: 'DELETE' }),
      ),
    );
  });

  it('opens the authoring flow seeded with the meal’s content when "Editar" is clicked (E5)', async () => {
    mockPolls();
    mockApi();
    render(<Wrapper />);

    await openEdit();

    expect(screen.getByLabelText(MESSAGES.RECIPE_AUTHORING_NAME_LABEL).value).toBe(
      'Lentejas al curry',
    );
    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_LIBRARY)).not.toBeNull();
    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH)).not.toBeNull();
    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_AI)).not.toBeNull();
  });

  it('PUTs the edited recipe to the meal’s own candidate endpoint (E6)', async () => {
    mockPolls();
    mockApi();
    render(<Wrapper />);
    await openEdit();

    fireEvent.change(screen.getByLabelText(MESSAGES.RECIPE_AUTHORING_NAME_LABEL), {
      target: { value: 'Lentejas estofadas' },
    });
    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        CANDIDATE_URL,
        expect.objectContaining({
          method: 'PUT',
          body: expect.objectContaining({
            recipe: expect.objectContaining({ name: 'Lentejas estofadas' }),
          }),
        }),
      ),
    );
  });

  it('applies the response ETag marker and closes the form after a successful edit (E9)', async () => {
    const applyMutationMarker = mockPolls();
    mockApi();
    render(<Wrapper />);
    await openEdit();

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));

    await waitFor(() => expect(applyMutationMarker).toHaveBeenCalledWith(21));
    await waitFor(() =>
      expect(screen.queryByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH)).toBeNull(),
    );
  });

  it('renders a rejected edit’s detail verbatim and keeps the form open (E10)', async () => {
    mockPolls();
    mockApi({
      onMutate: () =>
        Promise.reject(
          new ApiError({
            status: 404,
            code: 'CANDIDATE_NOT_FOUND',
            detail: 'Plato no encontrado.',
          }),
        ),
    });
    render(<Wrapper />);
    await openEdit();

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));

    await waitFor(() => expect(screen.getByText('Plato no encontrado.')).not.toBeNull());
    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH)).not.toBeNull();
  });

  it('asks for confirmation before removing a meal and sends nothing until it is confirmed (E7)', async () => {
    mockPolls();
    mockApi();
    render(<Wrapper />);

    await clickRemove();

    expect(screen.getByText(CONFIRM_REMOVE)).not.toBeNull();
    expect(mutationCalls()).toHaveLength(0);
  });

  it('DELETEs the meal and applies the response ETag marker once the removal is confirmed (E8, E9)', async () => {
    const applyMutationMarker = mockPolls();
    mockApi();
    render(<Wrapper />);
    await clickRemove();

    fireEvent.click(screen.getByText(MESSAGES.CONFIRM_DIALOG_CONFIRM));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        CANDIDATE_URL,
        expect.objectContaining({ method: 'DELETE' }),
      ),
    );
    await waitFor(() => expect(applyMutationMarker).toHaveBeenCalledWith(21));
  });

  it('renders a rejected removal’s detail verbatim (E10)', async () => {
    mockPolls();
    mockApi({
      onMutate: () =>
        Promise.reject(
          new ApiError({ status: 409, code: 'CONFLICT', detail: 'No se puede eliminar.' }),
        ),
    });
    render(<Wrapper />);
    await clickRemove();

    fireEvent.click(screen.getByText(MESSAGES.CONFIRM_DIALOG_CONFIRM));

    await waitFor(() => expect(screen.getByText('No se puede eliminar.')).not.toBeNull());
  });
});

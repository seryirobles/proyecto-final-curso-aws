// @vitest-environment jsdom
// Issue add-dish-button-inert (E1-E4): "Añadir plato" must open the
// three-method candidate authoring flow and POST to the slot's candidates
// endpoint. Driven through the real useWeekPlanner + WeekPlannerView pair.
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

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

const LIBRARY_RECIPE = {
  id: 'r-1',
  name: 'Lentejas al curry',
  category: 'legume',
  author: 'Marta',
};

const CANDIDATES_URL = '/v1/weeks/2026-W34/days/3/slots/1/candidates';

function Wrapper() {
  const planner = useWeekPlanner();
  return <WeekPlannerView {...planner} />;
}

// One marker sink per render, shared by the week poll and any library poll
// the authoring flow opens.
function mockPolls() {
  const applyMutationMarker = vi.fn();
  usePolling.mockImplementation((url) => ({
    data:
      url === '/v1/library/recipes'
        ? { recipes: [LIBRARY_RECIPE] }
        : { weekId: '2026-W34', slots: [] },
    marker: 1,
    connectionLost: false,
    applyMutationMarker,
  }));
  return applyMutationMarker;
}

function mockApi({ onPost } = {}) {
  apiFetch.mockImplementation((url, options) => {
    if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
    if (onPost) return onPost(url, options);
    options?.onHeaders?.(new Headers({ ETag: '"20"' }));
    return Promise.resolve({ candidate: { id: 'c9' }, duplicateWarning: false });
  });
}

// Day 3 / slot 1 is the fifth of the 14 add buttons (day-major order).
async function clickAddCandidate() {
  const buttons = await screen.findAllByText(MESSAGES.WEEK_PLANNER_ADD_CANDIDATE);
  fireEvent.click(buttons[4]);
}

describe('WeekPlannerView candidate authoring', () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it('opens the three-method authoring flow when "Añadir plato" is clicked (E1)', async () => {
    mockPolls();
    mockApi();
    render(<Wrapper />);
    await screen.findAllByText(MESSAGES.WEEK_PLANNER_ADD_CANDIDATE);

    expect(screen.queryByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH)).toBeNull();

    await clickAddCandidate();

    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_LIBRARY)).not.toBeNull();
    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH)).not.toBeNull();
    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_AI)).not.toBeNull();
  });

  it('POSTs a library pick to the clicked slot’s candidates endpoint (E2)', async () => {
    mockPolls();
    mockApi();
    render(<Wrapper />);
    await clickAddCandidate();

    fireEvent.click(screen.getByText(MESSAGES.LIBRARY_PICKER_SELECT));
    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        CANDIDATES_URL,
        expect.objectContaining({
          method: 'POST',
          body: { source: 'library', recipeId: 'r-1' },
        }),
      ),
    );
  });

  it('POSTs a from-scratch recipe as the manual source body (E2)', async () => {
    mockPolls();
    mockApi();
    render(<Wrapper />);
    await clickAddCandidate();

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH));
    fireEvent.change(screen.getByLabelText(MESSAGES.RECIPE_AUTHORING_NAME_LABEL), {
      target: { value: 'Tortilla' },
    });
    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        CANDIDATES_URL,
        expect.objectContaining({
          method: 'POST',
          body: expect.objectContaining({
            source: 'manual',
            recipe: expect.objectContaining({ name: 'Tortilla' }),
          }),
        }),
      ),
    );
  });

  it('applies the response ETag marker and closes the form after a successful add (E3)', async () => {
    const applyMutationMarker = mockPolls();
    mockApi();
    render(<Wrapper />);
    await clickAddCandidate();

    fireEvent.click(screen.getByText(MESSAGES.LIBRARY_PICKER_SELECT));
    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));

    await waitFor(() => expect(applyMutationMarker).toHaveBeenCalledWith(20));
    await waitFor(() =>
      expect(screen.queryByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH)).toBeNull(),
    );
  });

  it('renders the rejected add’s detail verbatim and keeps the form open (E4)', async () => {
    mockPolls();
    mockApi({
      onPost: () =>
        Promise.reject(new ApiError({ status: 409, code: 'CONFLICT', detail: 'Conflicto.' })),
    });
    render(<Wrapper />);
    await clickAddCandidate();

    fireEvent.click(screen.getByText(MESSAGES.LIBRARY_PICKER_SELECT));
    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));

    await waitFor(() => expect(screen.getByText('Conflicto.')).not.toBeNull());
    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH)).not.toBeNull();
  });
});

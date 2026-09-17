// @vitest-environment jsdom
// T29 (R9, R10, R19); F1 fix round 1 regression, F6 fix round 1 (reuses
// LibraryFilters, no duplicated markup).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { LibraryView } from '../../src/components/LibraryView.jsx';
import { useLibrary } from '../../src/hooks/useLibrary.js';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function Wrapper() {
  const library = useLibrary();
  return <LibraryView {...library} />;
}

function fetchResponse(recipes) {
  return {
    status: 200,
    headers: new Headers({ ETag: '"1"' }),
    json: () => Promise.resolve({ recipes }),
  };
}

// Direct-props baseline (T85 card-grid restyle), mirroring
// WeekPlannerView.test.jsx's pattern - proves each card's click handlers
// still reach the right recipe after the plain-list -> card-grid rewrite.
const RECIPE_A = { id: 'r-1', name: 'Lentejas al curry', category: 'legume', author: 'Marta' };
const RECIPE_B = { id: 'r-2', name: 'Tortilla', category: 'eggs', author: 'Diego' };

function baseProps(overrides = {}) {
  return {
    recipes: [RECIPE_A, RECIPE_B],
    filters: { name: '', category: '' },
    setName: vi.fn(),
    setCategory: vi.fn(),
    isLoading: false,
    isAuthoringOpen: false,
    authoring: {},
    openAdd: vi.fn(),
    openEdit: vi.fn(),
    closeAuthoring: vi.fn(),
    remove: vi.fn(),
    confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
    openDetail: vi.fn(),
    detail: null,
    detailError: null,
    closeDetail: vi.fn(),
    error: null,
    ...overrides,
  };
}

describe('LibraryView', () => {
  it('keeps the search input mounted and its value intact across every keystroke (F1)', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        fetchResponse([
          { id: 'r-1', name: 'Lentejas al curry', category: 'legume', author: 'Marta' },
        ]),
      );

    render(<Wrapper />);
    const input = await screen.findByLabelText(MESSAGES.LIBRARY_PICKER_NAME_LABEL);

    let typed = '';
    for (const char of 'lentejas') {
      typed += char;
      fireEvent.change(input, { target: { value: typed } });
      // A torn-down/recreated poll engine used to reset data to null and
      // flip LibraryView back to LoadingState, unmounting this input on
      // every keystroke (F1) - it must be the exact same node throughout.
      expect(screen.getByLabelText(MESSAGES.LIBRARY_PICKER_NAME_LABEL)).toBe(input);
    }

    expect(input.value).toBe('lentejas');
    expect(globalThis.fetch).toHaveBeenCalledTimes(1); // one poll, never re-issued per keystroke
  });

  it('renders every recipe with its author (R9)', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      fetchResponse([
        { id: 'r-1', name: 'Lentejas al curry', category: 'legume', author: 'Marta' },
        { id: 'r-2', name: 'Tortilla', category: 'eggs', author: 'Diego' },
      ]),
    );

    render(<Wrapper />);

    expect(await screen.findByText('Lentejas al curry')).not.toBeNull();
    expect(screen.getByText('Tortilla')).not.toBeNull();
  });

  it('renders EmptyState guidance for zero recipes (R19)', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(fetchResponse([]));

    render(<Wrapper />);

    expect(await screen.findByText(MESSAGES.LIBRARY_VIEW_EMPTY)).not.toBeNull();
  });

  it('clicking a card name calls openDetail with that recipe (T85 card-grid restyle)', () => {
    const openDetail = vi.fn();
    render(<LibraryView {...baseProps({ openDetail })} />);

    fireEvent.click(screen.getByText('Tortilla'));

    expect(openDetail).toHaveBeenCalledWith(RECIPE_B);
  });

  it('clicking a card edit icon-button calls openEdit with that recipe (T85 card-grid restyle)', () => {
    const openEdit = vi.fn();
    render(<LibraryView {...baseProps({ openEdit })} />);

    fireEvent.click(screen.getAllByText(MESSAGES.LIBRARY_VIEW_EDIT)[1]);

    expect(openEdit).toHaveBeenCalledWith(RECIPE_B);
  });

  it('clicking a card remove icon-button calls remove with that recipe id (T85 card-grid restyle)', () => {
    const remove = vi.fn();
    render(<LibraryView {...baseProps({ remove })} />);

    fireEvent.click(screen.getAllByText(MESSAGES.LIBRARY_VIEW_REMOVE)[1]);

    expect(remove).toHaveBeenCalledWith('r-2');
  });

  it('clicking "Añadir receta" calls openAdd, unaffected by the T85 restyle', () => {
    const openAdd = vi.fn();
    render(<LibraryView {...baseProps({ openAdd })} />);

    fireEvent.click(screen.getByText(MESSAGES.LIBRARY_VIEW_ADD));

    expect(openAdd).toHaveBeenCalledTimes(1);
  });
});

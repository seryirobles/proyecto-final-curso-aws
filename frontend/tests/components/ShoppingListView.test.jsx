// @vitest-environment jsdom
// T37 (R18, R19, R20, R21): two sections, add/edit/remove controls, resync
// loading state, empty state, WeekLabel-scoped resync copy.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, within } from '@testing-library/react';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { formatDate } from '../../src/locale.js';

afterEach(cleanup);

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function item(id, overrides = {}) {
  return { id, name: 'arroz', quantity: 500, unit: 'g', checked: false, ...overrides };
}

function baseProps(overrides = {}) {
  return {
    uncheckedItems: [],
    checkedItems: [],
    isLoading: false,
    liveWeeks: LIVE_WEEKS,
    isFormOpen: false,
    isEditing: false,
    draft: { name: '', quantity: '', unit: '' },
    updateDraftField: vi.fn(),
    canSaveItem: false,
    openAdd: vi.fn(),
    openEdit: vi.fn(),
    closeForm: vi.fn(),
    saveItem: vi.fn(),
    setChecked: vi.fn(),
    remove: vi.fn(),
    confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
    isResyncing: false,
    resync: vi.fn(),
    error: null,
    ...overrides,
  };
}

describe('ShoppingListView', () => {
  it('renders EmptyState when there are zero items (R19)', () => {
    render(<ShoppingListView {...baseProps()} />);

    expect(screen.getByText(MESSAGES.SHOPPING_LIST_VIEW_EMPTY)).not.toBeNull();
  });

  it('renders unchecked items in the unchecked section, checked items greyed out (FR-SHOP-08)', () => {
    render(
      <ShoppingListView
        {...baseProps({
          uncheckedItems: [item('s-1')],
          checkedItems: [item('s-2', { name: 'lentejas', checked: true })],
        })}
      />,
    );

    const uncheckedTitleIndex = screen
      .getAllByRole('heading')
      .findIndex((h) => h.textContent === MESSAGES.SHOPPING_LIST_UNCHECKED_SECTION_TITLE);
    const checkedTitleIndex = screen
      .getAllByRole('heading')
      .findIndex((h) => h.textContent === MESSAGES.SHOPPING_LIST_CHECKED_SECTION_TITLE);
    expect(uncheckedTitleIndex).toBeGreaterThan(-1);
    expect(checkedTitleIndex).toBeGreaterThan(uncheckedTitleIndex);

    const uncheckedRow = screen.getByText('arroz · 500 g').closest('li');
    expect(uncheckedRow.style.color).toBe(''); // s-1, unchecked, no grey style
  });

  it('places each item in its own section, not swapped (M2)', () => {
    render(
      <ShoppingListView
        {...baseProps({
          uncheckedItems: [item('s-1', { name: 'arroz' })],
          checkedItems: [item('s-2', { name: 'lentejas', checked: true })],
        })}
      />,
    );

    const uncheckedList = screen.getByText(
      MESSAGES.SHOPPING_LIST_UNCHECKED_SECTION_TITLE,
    ).nextElementSibling;
    const checkedList = screen.getByText(
      MESSAGES.SHOPPING_LIST_CHECKED_SECTION_TITLE,
    ).nextElementSibling;

    expect(within(uncheckedList).getByText('arroz · 500 g')).not.toBeNull();
    expect(within(uncheckedList).queryByText('lentejas · 500 g')).toBeNull();
    expect(within(checkedList).getByText('lentejas · 500 g')).not.toBeNull();
    expect(within(checkedList).queryByText('arroz · 500 g')).toBeNull();
  });

  it('a checked item is greyed out via tokens.color.ink3', () => {
    render(<ShoppingListView {...baseProps({ checkedItems: [item('s-2', { checked: true })] })} />);

    const row = screen.getByText('arroz · 500 g').closest('li');
    expect(row.style.color).toBe('rgb(144, 153, 125)'); // #90997D
  });

  it('remove routes through useConfirm (R18)', () => {
    const remove = vi.fn();
    render(<ShoppingListView {...baseProps({ uncheckedItems: [item('s-1')], remove })} />);

    fireEvent.click(screen.getByText(MESSAGES.SHOPPING_LIST_REMOVE));

    expect(remove).toHaveBeenCalledWith('s-1');
  });

  it('toggling a checkbox calls setChecked with the flipped value', () => {
    const setChecked = vi.fn();
    render(<ShoppingListView {...baseProps({ uncheckedItems: [item('s-1')], setChecked })} />);

    fireEvent.click(screen.getByRole('checkbox'));

    expect(setChecked).toHaveBeenCalledWith(item('s-1'), true);
  });

  it('clicking edit opens the item for editing', () => {
    const openEdit = vi.fn();
    render(<ShoppingListView {...baseProps({ uncheckedItems: [item('s-1')], openEdit })} />);

    fireEvent.click(screen.getByText(MESSAGES.SHOPPING_LIST_EDIT));

    expect(openEdit).toHaveBeenCalledWith(item('s-1'));
  });

  it('an in-flight resync renders LoadingState (R20)', () => {
    render(<ShoppingListView {...baseProps({ isResyncing: true })} />);

    expect(screen.getByText(MESSAGES.SHOPPING_LIST_RESYNC_IN_PROGRESS)).not.toBeNull();
    expect(screen.getByText(MESSAGES.SHOPPING_LIST_RESYNC).disabled).toBe(true);
  });

  it('the resync affordance renders a scoped intro, both WeekLabels and a connector between them (R21, decision 2)', () => {
    render(<ShoppingListView {...baseProps()} />);

    const currentExpected = `${MESSAGES.WEEK_LABEL_CURRENT} · ${formatDate(new Date(LIVE_WEEKS.current.monday))}–${formatDate(new Date(LIVE_WEEKS.current.sunday))}`;
    const nextExpected = `${MESSAGES.WEEK_LABEL_NEXT} · ${formatDate(new Date(LIVE_WEEKS.next.monday))}–${formatDate(new Date(LIVE_WEEKS.next.sunday))}`;
    // The intro text scopes "desde hoy" - the current-week label's full
    // Monday-Sunday range never stands alone implying it's all in scope.
    expect(screen.getByText(MESSAGES.SHOPPING_LIST_RESYNC_SCOPE_LABEL)).not.toBeNull();
    expect(screen.getByText(currentExpected)).not.toBeNull();
    expect(screen.getByText(MESSAGES.SHOPPING_LIST_RESYNC_SCOPE_CONNECTOR)).not.toBeNull();
    expect(screen.getByText(nextExpected)).not.toBeNull();
  });

  it('clicking resync calls resync', () => {
    const resync = vi.fn();
    render(<ShoppingListView {...baseProps({ resync })} />);

    fireEvent.click(screen.getByText(MESSAGES.SHOPPING_LIST_RESYNC));

    expect(resync).toHaveBeenCalled();
  });

  it('renders the item form when isFormOpen is true, pre-filled from the draft', () => {
    render(
      <ShoppingListView
        {...baseProps({
          isFormOpen: true,
          isEditing: true,
          draft: { name: 'lentejas', quantity: '300', unit: 'g' },
        })}
      />,
    );

    expect(screen.getByDisplayValue('lentejas')).not.toBeNull();
    expect(screen.getByDisplayValue('300')).not.toBeNull();
    expect(screen.getByText(MESSAGES.SHOPPING_LIST_SAVE_EDIT)).not.toBeNull();
  });

  it('renders the caught error text (R15)', () => {
    render(<ShoppingListView {...baseProps({ error: 'Bloqueado.' })} />);

    expect(screen.getByText('Bloqueado.')).not.toBeNull();
  });

  it('renders ConfirmDialog only when a removal is pending (R18)', () => {
    render(
      <ShoppingListView
        {...baseProps({
          uncheckedItems: [item('s-1')],
          confirm: {
            pending: { message: MESSAGES.CONFIRM_REMOVE_SHOPPING_ITEM },
            confirm: vi.fn(),
            cancel: vi.fn(),
          },
        })}
      />,
    );

    expect(screen.getByText(MESSAGES.CONFIRM_REMOVE_SHOPPING_ITEM)).not.toBeNull();
  });
});

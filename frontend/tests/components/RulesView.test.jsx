// @vitest-environment jsdom
// T33/T34 (R12, R18, R19): rule list, dropdown-only add controls, EmptyState
// for zero rules, and the pin field reaching LibraryRecipePicker (T27/T31's
// shared component, closing the 3rd of 3 sites).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { RulesView } from '../../src/components/RulesView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

function baseProps(overrides = {}) {
  return {
    categoryCounts: [],
    pins: [],
    disabledDays: [],
    isLoading: false,
    error: null,
    confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
    remove: vi.fn(),
    picker: {
      filters: { name: '', category: '' },
      setName: vi.fn(),
      setCategory: vi.fn(),
      recipes: [],
      allRecipes: [],
      isLoading: false,
      connectionLost: false,
    },
    categoryCountDraft: { category: '', count: '' },
    setCategoryCountCategory: vi.fn(),
    setCategoryCountCount: vi.fn(),
    canSaveCategoryCount: false,
    saveCategoryCount: vi.fn(),
    pinDraft: { day: '', slot: '' },
    setPinDay: vi.fn(),
    setPinSlot: vi.fn(),
    pinRecipeId: null,
    selectPinRecipe: vi.fn(),
    canSavePin: false,
    savePin: vi.fn(),
    disabledDayDraft: { day: '' },
    setDisabledDayDay: vi.fn(),
    canSaveDisabledDay: false,
    saveDisabledDay: vi.fn(),
    ...overrides,
  };
}

describe('RulesView', () => {
  it('renders EmptyState when there are zero rules (R19)', () => {
    render(<RulesView {...baseProps()} />);

    expect(screen.getByText(MESSAGES.RULES_VIEW_EMPTY)).not.toBeNull();
  });

  it('renders an existing category-count rule and removes it through remove()', () => {
    const remove = vi.fn();
    render(
      <RulesView
        {...baseProps({
          categoryCounts: [{ type: 'categoryCount', category: 'meat', count: 2 }],
          remove,
        })}
      />,
    );

    expect(screen.getByText('Carne × 2')).not.toBeNull();
    fireEvent.click(screen.getByText(MESSAGES.RULES_REMOVE));

    expect(remove).toHaveBeenCalledWith({ type: 'categoryCount', category: 'meat', count: 2 });
  });

  it('renders a pin rule using recipeName straight off the API response', () => {
    render(
      <RulesView
        {...baseProps({
          pins: [{ type: 'pin', day: 1, slot: 1, recipeId: 'r-1', recipeName: 'Tortilla' }],
        })}
      />,
    );

    // GET /v1/rules resolves recipeName server-side (data_model.md section
    // 6); asserts the composed row label, not just "Tortilla" appearing.
    expect(screen.getByText('lunes · Comida · Tortilla')).not.toBeNull();
  });

  it('every save control is disabled until its own canSave* flag is true', () => {
    render(<RulesView {...baseProps()} />);

    const saveButtons = screen.getAllByText(MESSAGES.RULES_SAVE);
    expect(saveButtons[0].disabled).toBe(true); // category count
    expect(saveButtons[1].disabled).toBe(true); // pin
    expect(saveButtons[2].disabled).toBe(true); // disabled day
  });

  it('clicking the pin save button calls savePin, not the other save handlers', () => {
    const savePin = vi.fn();
    const saveCategoryCount = vi.fn();
    const saveDisabledDay = vi.fn();
    render(
      <RulesView
        {...baseProps({ savePin, saveCategoryCount, saveDisabledDay, canSavePin: true })}
      />,
    );

    fireEvent.click(screen.getAllByText(MESSAGES.RULES_SAVE)[1]);

    expect(savePin).toHaveBeenCalledTimes(1);
    expect(saveCategoryCount).not.toHaveBeenCalled();
    expect(saveDisabledDay).not.toHaveBeenCalled();
  });

  it("the pin field embeds LibraryRecipePicker - same shared component as T27/T31's sites (R12)", () => {
    render(
      <RulesView
        {...baseProps({
          picker: {
            ...baseProps().picker,
            recipes: [
              { id: 'r-1', name: 'Lentejas al curry', category: 'legume', author: 'Marta' },
            ],
          },
        })}
      />,
    );

    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_NAME_LABEL)).not.toBeNull();
    expect(screen.getByText('Lentejas al curry')).not.toBeNull();
  });

  it('selecting a recipe from the pin picker calls selectPinRecipe (R12)', () => {
    const selectPinRecipe = vi.fn();
    render(
      <RulesView
        {...baseProps({
          selectPinRecipe,
          picker: {
            ...baseProps().picker,
            recipes: [
              { id: 'r-1', name: 'Lentejas al curry', category: 'legume', author: 'Marta' },
            ],
          },
        })}
      />,
    );

    fireEvent.click(screen.getByText(MESSAGES.LIBRARY_PICKER_SELECT));

    expect(selectPinRecipe).toHaveBeenCalledWith('r-1');
  });

  it('every rule-defining control is a dropdown, never free text (T33, FR-RULE-03)', () => {
    render(<RulesView {...baseProps()} />);

    // The only free-text input on the page is the pin picker's own search
    // box (LibraryFilters) - a separate, already-covered concern (T31).
    const textInputs = screen.getAllByRole('textbox');
    expect(textInputs).toHaveLength(1);
    expect(screen.getByRole('textbox', { name: MESSAGES.LIBRARY_PICKER_NAME_LABEL })).toBe(
      textInputs[0],
    );

    // Category, count, pin-day, pin-slot, disabled-day, plus the picker's
    // own category filter - every rule-defining field is a <select>.
    expect(screen.getAllByRole('combobox')).toHaveLength(6);
  });

  it("a pin row's recipeName is unaffected by the picker's own search filter (finding 6)", () => {
    render(
      <RulesView
        {...baseProps({
          pins: [{ type: 'pin', day: 1, slot: 1, recipeId: 'r-1', recipeName: 'Tortilla' }],
          picker: {
            ...baseProps().picker,
            filters: { name: 'zzz-no-match', category: '' },
            recipes: [], // filtered out of the picker's own visible list, for a NEW pin
          },
        })}
      />,
    );

    expect(screen.getByText('lunes · Comida · Tortilla')).not.toBeNull();
  });

  it('with two category-count rules, removing the SECOND row targets it, not the first (T91 card restyle)', () => {
    const remove = vi.fn();
    const ruleA = { type: 'categoryCount', category: 'meat', count: 2 };
    const ruleB = { type: 'categoryCount', category: 'fish', count: 1 };
    render(<RulesView {...baseProps({ categoryCounts: [ruleA, ruleB], remove })} />);

    const removeButtons = screen.getAllByText(MESSAGES.RULES_REMOVE);
    fireEvent.click(removeButtons[1]);

    expect(remove).toHaveBeenCalledWith(ruleB);
    expect(remove).not.toHaveBeenCalledWith(ruleA);
  });

  it('removes a pin rule through remove()', () => {
    const remove = vi.fn();
    const pinRule = { type: 'pin', day: 1, slot: 1, recipeId: 'r-1', recipeName: 'Tortilla' };
    render(<RulesView {...baseProps({ pins: [pinRule], remove })} />);

    fireEvent.click(screen.getByText(MESSAGES.RULES_REMOVE));

    expect(remove).toHaveBeenCalledWith(pinRule);
  });

  it('renders a disabled-day rule and removes it through remove()', () => {
    const remove = vi.fn();
    render(
      <RulesView {...baseProps({ disabledDays: [{ type: 'disabledDay', day: 7 }], remove })} />,
    );

    fireEvent.click(screen.getByText(MESSAGES.RULES_REMOVE));

    expect(remove).toHaveBeenCalledWith({ type: 'disabledDay', day: 7 });
  });

  it('with two disabled-day rules, removing the SECOND row targets it, not the first', () => {
    const remove = vi.fn();
    const ruleA = { type: 'disabledDay', day: 6 };
    const ruleB = { type: 'disabledDay', day: 7 };
    render(<RulesView {...baseProps({ disabledDays: [ruleA, ruleB], remove })} />);

    const removeButtons = screen.getAllByText(MESSAGES.RULES_REMOVE);
    fireEvent.click(removeButtons[1]);

    expect(remove).toHaveBeenCalledWith(ruleB);
    expect(remove).not.toHaveBeenCalledWith(ruleA);
  });

  it('renders the caught error text (R15)', () => {
    render(<RulesView {...baseProps({ error: 'Día no válido.' })} />);

    expect(screen.getByText('Día no válido.')).not.toBeNull();
  });

  it('renders ConfirmDialog only when a removal is pending (R18)', () => {
    render(
      <RulesView
        {...baseProps({
          disabledDays: [{ type: 'disabledDay', day: 7 }],
          confirm: {
            pending: { message: MESSAGES.CONFIRM_REMOVE_RULE },
            confirm: vi.fn(),
            cancel: vi.fn(),
          },
        })}
      />,
    );

    expect(screen.getByText(MESSAGES.CONFIRM_REMOVE_RULE)).not.toBeNull();
  });
});

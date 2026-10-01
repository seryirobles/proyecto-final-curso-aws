// @vitest-environment jsdom
// R33: the button that triggers a pending mutation is disabled meanwhile.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MESSAGES } from '../../src/messages/index.js';
import { tokens } from '../../src/tokens/index.js';
import { WeekPlannerView } from '../../src/components/WeekPlannerView.jsx';
import { LibraryView } from '../../src/components/LibraryView.jsx';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';
import { RulesView } from '../../src/components/RulesView.jsx';
import { AdminAccountsView } from '../../src/components/AdminAccountsView.jsx';
import { RecipeAuthoringForm } from '../../src/components/RecipeAuthoringForm.jsx';

afterEach(cleanup);

const noop = vi.fn();
const confirm = { pending: null, confirm: noop, cancel: noop };
const picker = {
  filters: { name: '', category: '' },
  setName: noop,
  setCategory: noop,
  recipes: [],
  allRecipes: [],
  isLoading: false,
  connectionLost: false,
};

function buttonOf(text) {
  return screen.getByText(text).closest('button');
}

function weekProps(pending) {
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
  const days = Array.from({ length: 7 }, (_, i) => ({
    day: i + 1,
    slots: [
      {
        slot: 1,
        candidates: i === 0 ? [candidate] : [],
        definitiveId: null,
        isEmpty: i !== 0,
      },
      { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
    ],
  }));
  return {
    liveWeeks: {
      today: '2026-08-17',
      current: { weekId: 'w', monday: '2026-08-17', sunday: '2026-08-23' },
      next: { weekId: 'x', monday: '2026-08-24', sunday: '2026-08-30' },
    },
    designation: 'current',
    week: { weekId: 'w', days },
    isLoading: false,
    switchWeek: noop,
    openCandidateAuthoring: noop,
    openDetail: noop,
    promoteDefinitive: noop,
    clearDefinitive: noop,
    removeCandidate: noop,
    openCandidateEdit: noop,
    confirm,
    detail: null,
    closeDetail: noop,
    error: null,
    pending,
  };
}

function libraryProps(pending) {
  return {
    recipes: [{ id: 'r-1', name: 'Tortilla', category: 'eggs', author: 'Diego' }],
    filters: { name: '', category: '' },
    setName: noop,
    setCategory: noop,
    isLoading: false,
    isAuthoringOpen: false,
    isEditing: false,
    authoring: {},
    openAdd: noop,
    openEdit: noop,
    closeAuthoring: noop,
    remove: noop,
    confirm,
    openDetail: noop,
    detail: null,
    detailError: null,
    closeDetail: noop,
    error: null,
    pending,
  };
}

function shoppingProps(pending, overrides = {}) {
  return {
    uncheckedItems: [{ id: 's-1', name: 'arroz', quantity: 1, unit: 'g', checked: false }],
    checkedItems: [],
    isLoading: false,
    liveWeeks: null,
    isFormOpen: false,
    isEditing: false,
    draft: { name: 'a', quantity: '1', unit: 'g' },
    updateDraftField: noop,
    canSaveItem: true,
    openAdd: noop,
    openEdit: noop,
    closeForm: noop,
    saveItem: noop,
    setChecked: noop,
    remove: noop,
    confirm,
    isResyncing: false,
    resync: noop,
    error: null,
    pending,
    ...overrides,
  };
}

function rulesProps(pending) {
  return {
    categoryCounts: [],
    pins: [],
    disabledDays: [],
    isLoading: false,
    error: null,
    confirm,
    remove: noop,
    picker,
    categoryCountDraft: { category: '', count: '' },
    categoryCountOptions: [],
    setCategoryCountCategory: noop,
    setCategoryCountCount: noop,
    canSaveCategoryCount: true,
    saveCategoryCount: noop,
    pinDraft: { day: '', slot: '' },
    pinDayOptions: [],
    setPinDay: noop,
    setPinSlot: noop,
    pinRecipeId: null,
    selectPinRecipe: noop,
    canSavePin: true,
    savePin: noop,
    disabledDayDraft: { day: '' },
    disabledDayOptions: [],
    setDisabledDayDay: noop,
    canSaveDisabledDay: true,
    saveDisabledDay: noop,
    pending,
  };
}

function adminProps(pending, overrides = {}) {
  return {
    accounts: [{ userId: 'u-2', username: 'beto', role: 'User', passwordResetRequired: false }],
    isLoading: false,
    error: null,
    actingUserId: 'a',
    newUsername: 'x',
    setNewUsername: noop,
    newTemporaryPassword: 'y',
    setNewTemporaryPassword: noop,
    canCreate: true,
    create: noop,
    renamingId: null,
    renameDraft: 'z',
    setRenameDraft: noop,
    canSaveRename: true,
    openRename: noop,
    saveRename: noop,
    cancelRename: noop,
    resettingId: null,
    resetDraft: 'z',
    setResetDraft: noop,
    canSaveReset: true,
    openReset: noop,
    saveReset: noop,
    cancelReset: noop,
    remove: noop,
    confirm,
    pending,
    ...overrides,
  };
}

describe('trigger buttons disabled while pending (R33)', () => {
  it('Week: promote and remove of the pending meal', () => {
    render(<WeekPlannerView {...weekProps(new Set(['promote:1:1', 'remove:c1']))} />);

    expect(buttonOf(MESSAGES.WEEK_PLANNER_PROMOTE_DEFINITIVE).disabled).toBe(true);
    expect(buttonOf(MESSAGES.WEEK_PLANNER_REMOVE_CANDIDATE).disabled).toBe(true);
    expect(buttonOf(MESSAGES.WEEK_PLANNER_EDIT_CANDIDATE).disabled).toBe(false);
    cleanup();

    render(<WeekPlannerView {...weekProps(new Set())} />);
    expect(buttonOf(MESSAGES.WEEK_PLANNER_PROMOTE_DEFINITIVE).disabled).toBe(false);
    expect(buttonOf(MESSAGES.WEEK_PLANNER_REMOVE_CANDIDATE).disabled).toBe(false);
  });

  it('Library: remove of the pending recipe', () => {
    render(<LibraryView {...libraryProps(new Set(['remove:r-1']))} />);
    expect(buttonOf(MESSAGES.LIBRARY_VIEW_REMOVE).disabled).toBe(true);
    cleanup();

    render(<LibraryView {...libraryProps(new Set())} />);
    expect(buttonOf(MESSAGES.LIBRARY_VIEW_REMOVE).disabled).toBe(false);
  });

  it('Authoring form: save button while the submit is pending', () => {
    const props = {
      mode: 'library',
      methods: ['scratch'],
      method: 'scratch',
      setMethod: noop,
      form: {
        name: '',
        category: '',
        servings: '',
        estimatedTime: '',
        ingredients: [],
        tools: [],
        procedure: [],
      },
      updateField: noop,
      addIngredient: noop,
      updateIngredient: noop,
      removeIngredient: noop,
      addTool: noop,
      updateTool: noop,
      removeTool: noop,
      addProcedureStep: noop,
      updateProcedureStep: noop,
      removeProcedureStep: noop,
      libraryPicker: picker,
      referencePicker: picker,
      aiSpec: { ingredients: '', tools: '', notes: '' },
      updateAiSpec: noop,
      canSubmit: true,
      submit: noop,
    };
    render(<RecipeAuthoringForm {...props} pending={new Set(['submit'])} />);
    expect(buttonOf(MESSAGES.RECIPE_AUTHORING_SUBMIT).disabled).toBe(true);
    cleanup();

    render(<RecipeAuthoringForm {...props} pending={new Set()} />);
    expect(buttonOf(MESSAGES.RECIPE_AUTHORING_SUBMIT).disabled).toBe(false);
  });

  it('Shopping: remove, re-sync and the item save', () => {
    render(<ShoppingListView {...shoppingProps(new Set(['remove:s-1', 'resync']))} />);
    expect(buttonOf(MESSAGES.SHOPPING_LIST_REMOVE).disabled).toBe(true);
    expect(buttonOf(MESSAGES.SHOPPING_LIST_RESYNC).disabled).toBe(true);
    cleanup();

    render(<ShoppingListView {...shoppingProps(new Set(['saveItem']), { isFormOpen: true })} />);
    expect(buttonOf(MESSAGES.SHOPPING_LIST_SAVE_ADD).disabled).toBe(true);
    cleanup();

    render(<ShoppingListView {...shoppingProps(new Set(), { isFormOpen: true })} />);
    expect(buttonOf(MESSAGES.SHOPPING_LIST_SAVE_ADD).disabled).toBe(false);
  });

  it('Rules: each save button follows its own key', () => {
    render(<RulesView {...rulesProps(new Set(['savePin']))} />);
    const [category, pin, day] = screen
      .getAllByText(MESSAGES.RULES_SAVE)
      .map((el) => el.closest('button'));

    expect(category.disabled).toBe(false);
    expect(pin.disabled).toBe(true);
    expect(day.disabled).toBe(false);
    cleanup();

    render(<RulesView {...rulesProps(new Set(['saveCategoryCount', 'saveDisabledDay']))} />);
    const buttons = screen.getAllByText(MESSAGES.RULES_SAVE).map((el) => el.closest('button'));
    expect(buttons.map((b) => b.disabled)).toEqual([true, false, true]);
  });

  it('Admin: create, rename-save, reset-save and remove', () => {
    render(<AdminAccountsView {...adminProps(new Set(['create', 'remove:u-2']))} />);
    expect(buttonOf(MESSAGES.ADMIN_ACCOUNTS_CREATE).disabled).toBe(true);
    expect(buttonOf(MESSAGES.ADMIN_ACCOUNTS_REMOVE).disabled).toBe(true);
    cleanup();

    render(<AdminAccountsView {...adminProps(new Set(['saveRename']), { renamingId: 'u-2' })} />);
    const rename = screen
      .getAllByText(MESSAGES.ADMIN_ACCOUNTS_RENAME)
      .map((el) => el.closest('button'));
    expect(rename.some((b) => b.type === 'submit' && b.disabled)).toBe(true);
    cleanup();

    render(<AdminAccountsView {...adminProps(new Set(['saveReset']), { resettingId: 'u-2' })} />);
    const reset = screen
      .getAllByText(MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD)
      .map((el) => el.closest('button'));
    expect(reset.some((b) => b.type === 'submit' && b.disabled)).toBe(true);
  });

  it('Rules: a rule remove button follows its own remove key (R33)', () => {
    const rules = {
      ...rulesProps(new Set(['remove:cat#meat'])),
      categoryCounts: [{ type: 'categoryCount', category: 'meat', count: 2 }],
      disabledDays: [{ type: 'disabledDay', day: 2 }],
    };
    render(<RulesView {...rules} />);

    const removes = screen.getAllByText(MESSAGES.RULES_REMOVE).map((el) => el.closest('button'));
    expect(removes.map((b) => b.disabled)).toEqual([true, false]);
  });

  it('Authoring submit shows the disabled look when invalid or pending (R30)', () => {
    const base = {
      mode: 'library',
      methods: ['scratch'],
      method: 'scratch',
      setMethod: noop,
      form: {
        name: '',
        category: '',
        servings: '',
        estimatedTime: '',
        ingredients: [],
        tools: [],
        procedure: [],
      },
      updateField: noop,
      addIngredient: noop,
      updateIngredient: noop,
      removeIngredient: noop,
      addTool: noop,
      updateTool: noop,
      removeTool: noop,
      addProcedureStep: noop,
      updateProcedureStep: noop,
      removeProcedureStep: noop,
      libraryPicker: picker,
      referencePicker: picker,
      aiSpec: { ingredients: '', tools: '', notes: '' },
      updateAiSpec: noop,
      submit: noop,
    };
    const cases = [
      { canSubmit: false, pending: new Set(), disabled: true },
      { canSubmit: true, pending: new Set(['submit']), disabled: true },
      { canSubmit: true, pending: new Set(), disabled: false },
    ];
    for (const { disabled, ...rest } of cases) {
      render(<RecipeAuthoringForm {...base} {...rest} />);
      const style = buttonOf(MESSAGES.RECIPE_AUTHORING_SUBMIT).style;
      expect(style.cursor).toBe(disabled ? 'not-allowed' : '');
      expect(style.opacity).toBe(disabled ? String(tokens.opacity.disabled) : '');
      cleanup();
    }
  });
});

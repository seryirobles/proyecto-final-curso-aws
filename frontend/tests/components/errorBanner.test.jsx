// @vitest-environment jsdom
// R34, R36, R40, R42, R43: each view shows its hook error in a Banner, placed
// per design.md section 3 (above the open form, else below the heading).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MESSAGES } from '../../src/messages/index.js';

vi.mock('../../src/components/CandidateAuthoring.jsx', () => ({
  CandidateAuthoring: () => <section>CANDIDATE_FORM_MARKER</section>,
}));

import { WeekPlannerView } from '../../src/components/WeekPlannerView.jsx';
import { LibraryView } from '../../src/components/LibraryView.jsx';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';
import { AdminAccountsView } from '../../src/components/AdminAccountsView.jsx';
import { RulesView } from '../../src/components/RulesView.jsx';
import { SummaryView } from '../../src/components/SummaryView.jsx';
import { LoginView } from '../../src/components/LoginView.jsx';
import { SetPasswordView } from '../../src/components/SetPasswordView.jsx';

afterEach(cleanup);

const ERR = MESSAGES.GENERIC_ERROR;
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

// True when `a` comes before `b` in document order.
function before(a, b) {
  return Boolean(a.compareDocumentPosition(b) & a.DOCUMENT_POSITION_FOLLOWING);
}

function expectAlertBefore(target) {
  const alert = screen.getByRole('alert');
  expect(alert.textContent).toContain(ERR);
  expect(before(alert, target)).toBe(true);
}

function expectAlertAfter(heading) {
  const alert = screen.getByRole('alert');
  expect(alert.textContent).toContain(ERR);
  expect(before(heading, alert)).toBe(true);
}

const week = {
  weekId: 'w',
  days: Array.from({ length: 7 }, (_, i) => ({
    day: i + 1,
    slots: [
      { slot: 1, candidates: [], definitiveId: null, isEmpty: true },
      { slot: 2, candidates: [], definitiveId: null, isEmpty: true },
    ],
  })),
};

function weekProps(overrides = {}) {
  return {
    liveWeeks: {
      today: '2026-08-17',
      current: { weekId: 'w', monday: '2026-08-17', sunday: '2026-08-23' },
      next: { weekId: 'x', monday: '2026-08-24', sunday: '2026-08-30' },
    },
    designation: 'current',
    week,
    isLoading: false,
    switchWeek: noop,
    openCandidateAuthoring: noop,
    openDetail: noop,
    promoteDefinitive: noop,
    clearDefinitive: noop,
    confirm,
    detail: null,
    closeDetail: noop,
    error: null,
    ...overrides,
  };
}

function libraryProps(overrides = {}) {
  return {
    recipes: [],
    filters: { name: '', category: '' },
    setName: noop,
    setCategory: noop,
    isLoading: false,
    isAuthoringOpen: false,
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
    ...overrides,
  };
}

function authoringProps() {
  return {
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
    canSubmit: false,
    submit: noop,
  };
}

function shoppingProps(overrides = {}) {
  return {
    uncheckedItems: [],
    checkedItems: [],
    isLoading: false,
    liveWeeks: null,
    isFormOpen: false,
    isEditing: false,
    draft: { name: '', quantity: '', unit: '' },
    updateDraftField: noop,
    canSaveItem: false,
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
    ...overrides,
  };
}

function adminProps(overrides = {}) {
  return {
    accounts: [],
    isLoading: false,
    error: null,
    actingUserId: 'a',
    newUsername: '',
    setNewUsername: noop,
    newTemporaryPassword: '',
    setNewTemporaryPassword: noop,
    canCreate: false,
    create: noop,
    confirm,
    ...overrides,
  };
}

function rulesProps(overrides = {}) {
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
    canSaveCategoryCount: false,
    saveCategoryCount: noop,
    pinDraft: { day: '', slot: '' },
    pinDayOptions: [],
    setPinDay: noop,
    setPinSlot: noop,
    pinRecipeId: null,
    selectPinRecipe: noop,
    canSavePin: false,
    savePin: noop,
    disabledDayDraft: { day: '' },
    disabledDayOptions: [],
    setDisabledDayDay: noop,
    canSaveDisabledDay: false,
    saveDisabledDay: noop,
    ...overrides,
  };
}

function summaryProps(overrides = {}) {
  return {
    week: { weekId: 'w', monday: '2026-08-17', sunday: '2026-08-23' },
    summary: { weekId: 'w', days: [], isEmpty: true },
    isLoading: false,
    openDetail: noop,
    detail: null,
    closeDetail: noop,
    error: null,
    ...overrides,
  };
}

function loginProps(overrides = {}) {
  return {
    username: '',
    setUsername: noop,
    password: '',
    setPassword: noop,
    canSubmit: true,
    submit: noop,
    error: null,
    isSubmitting: false,
    ...overrides,
  };
}

function setPasswordProps(overrides = {}) {
  return {
    status: 'passwordResetPending',
    newPassword: '',
    setNewPassword: noop,
    confirmPassword: '',
    setConfirmPassword: noop,
    mismatch: false,
    canSubmit: true,
    submit: noop,
    cancel: noop,
    error: null,
    isSubmitting: false,
    ...overrides,
  };
}

describe('error Banner in each view', () => {
  it('Week: alert above the open candidate form, none without an error (R34, R36, R43)', () => {
    render(
      <WeekPlannerView {...weekProps({ error: ERR, authoringTarget: { day: 1, slot: 1 } })} />,
    );
    expectAlertBefore(screen.getByText('CANDIDATE_FORM_MARKER'));
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    cleanup();

    render(
      <WeekPlannerView
        {...weekProps({ error: ERR, editingTarget: { day: 1, slot: 1, recipe: {} } })}
      />,
    );
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    expect(screen.getByRole('alert').nextElementSibling).toBe(
      screen.getByText('CANDIDATE_FORM_MARKER'),
    );
    cleanup();

    render(<WeekPlannerView {...weekProps({ error: ERR })} />);
    expect(screen.getByRole('alert').textContent).toContain(ERR);
    cleanup();

    render(<WeekPlannerView {...weekProps()} />);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('Library: alert above the open authoring form, else below the heading (R36, R43)', () => {
    render(
      <LibraryView
        {...libraryProps({ error: ERR, isAuthoringOpen: true, authoring: authoringProps() })}
      />,
    );
    expectAlertBefore(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH));
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    cleanup();

    render(<LibraryView {...libraryProps({ error: ERR })} />);
    expectAlertAfter(screen.getByText(MESSAGES.LIBRARY_VIEW_TITLE));
    cleanup();

    render(<LibraryView {...libraryProps()} />);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('Shopping: alert above the open item form, else below the heading (R36, R43)', () => {
    render(<ShoppingListView {...shoppingProps({ error: ERR, isFormOpen: true })} />);
    expectAlertBefore(screen.getByText(MESSAGES.SHOPPING_LIST_NAME_LABEL));
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    cleanup();

    render(<ShoppingListView {...shoppingProps({ error: ERR })} />);
    expectAlertAfter(screen.getByText(MESSAGES.SHOPPING_LIST_VIEW_TITLE));
    cleanup();

    render(<ShoppingListView {...shoppingProps()} />);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('Admin: alert below the heading, above the create form (R36, R43)', () => {
    render(<AdminAccountsView {...adminProps({ error: ERR })} />);
    expectAlertAfter(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_VIEW_TITLE));
    expectAlertBefore(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_CREATE));
    cleanup();

    render(<AdminAccountsView {...adminProps()} />);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('Admin: rename/reset failure renders inside the open row, not at the top (R36)', () => {
    const accounts = [
      { userId: 'u-1', username: 'ana', role: 'User', passwordResetRequired: false },
      { userId: 'u-2', username: 'beto', role: 'User', passwordResetRequired: false },
    ];
    for (const open of [{ renamingId: 'u-2' }, { resettingId: 'u-2' }]) {
      render(<AdminAccountsView {...adminProps({ accounts, error: ERR, ...open })} />);

      const alerts = screen.getAllByRole('alert');
      expect(alerts).toHaveLength(1);
      const row = alerts[0].closest('li');
      expect(row.textContent).toContain('beto');
      expect(row.querySelector('input')).not.toBeNull();
      expect(before(alerts[0], row.querySelector('input'))).toBe(true);
      cleanup();
    }
  });

  it('Rules: alert below the heading, above the rule forms (R36, R43)', () => {
    render(<RulesView {...rulesProps({ error: ERR })} />);
    expectAlertBefore(screen.getAllByText(MESSAGES.RULES_SAVE)[0]);
    cleanup();

    render(<RulesView {...rulesProps()} />);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('Summary: alert after the heading (R36, R43)', () => {
    render(<SummaryView {...summaryProps({ error: ERR })} />);
    expectAlertAfter(screen.getByText(MESSAGES.SUMMARY_VIEW_TITLE));
    cleanup();

    render(<SummaryView {...summaryProps()} />);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('Login: alert above the submit button (R36, R43)', () => {
    render(<LoginView {...loginProps({ error: ERR })} />);
    expectAlertBefore(screen.getByText(MESSAGES.LOGIN_SUBMIT));
    expectAlertAfter(screen.getByLabelText(MESSAGES.LOGIN_PASSWORD_LABEL));
    cleanup();

    render(<LoginView {...loginProps()} />);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('Set-password: alert above the submit button (R36, R43)', () => {
    render(<SetPasswordView {...setPasswordProps({ error: ERR })} />);
    expectAlertBefore(screen.getByText(MESSAGES.SET_PASSWORD_SUBMIT));
    expectAlertAfter(screen.getByLabelText(MESSAGES.SET_PASSWORD_CONFIRM_LABEL));
    cleanup();

    render(<SetPasswordView {...setPasswordProps()} />);
    expect(screen.queryByRole('alert')).toBeNull();
  });
});

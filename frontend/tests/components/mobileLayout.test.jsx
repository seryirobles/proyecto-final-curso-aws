// @vitest-environment jsdom
// R4-R6: wrap/grid/box-sizing style assertions (jsdom has no layout).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { tokens } from '../../src/tokens/index.js';
import { MESSAGES } from '../../src/messages/index.js';
import { RulesView } from '../../src/components/RulesView.jsx';
import { AccountRow } from '../../src/components/AccountRow.jsx';
import { AdminAccountsView } from '../../src/components/AdminAccountsView.jsx';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';
import { AiRecipePreview } from '../../src/components/AiRecipePreview.jsx';
import { RecipeAuthoringForm } from '../../src/components/RecipeAuthoringForm.jsx';
import { SummaryView } from '../../src/components/SummaryView.jsx';
import { LoginView } from '../../src/components/LoginView.jsx';
import { SetPasswordView } from '../../src/components/SetPasswordView.jsx';
import { inputStyle, selectStyle } from '../../src/tokens/controlStyles.js';

afterEach(cleanup);

const noop = vi.fn();
const picker = {
  filters: { name: '', category: '' },
  setName: noop,
  setCategory: noop,
  recipes: [],
  allRecipes: [],
  isLoading: false,
  connectionLost: false,
};
const confirm = { pending: null, confirm: noop, cancel: noop };

function rulesProps() {
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
  };
}

function accountRowProps() {
  return {
    account: { userId: 'u-1', username: 'ana', role: 'User', passwordResetRequired: false },
    actingUserId: 'admin-1',
    isRenaming: false,
    renameDraft: '',
    onRenameDraftChange: noop,
    canSaveRename: false,
    onOpenRename: noop,
    onSaveRename: noop,
    onCancelRename: noop,
    isResetting: false,
    resetDraft: '',
    onResetDraftChange: noop,
    canSaveReset: false,
    onOpenReset: noop,
    onSaveReset: noop,
    onCancelReset: noop,
    onRemove: noop,
  };
}

function authoringProps() {
  return {
    mode: 'candidate',
    methods: ['library', 'scratch', 'ai'],
    method: 'scratch',
    setMethod: noop,
    form: {
      name: '',
      category: '',
      servings: '',
      estimatedTime: '',
      ingredients: [{ name: '', quantity: '', unit: '' }],
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
    libraryRecipeId: null,
    selectLibraryRecipe: noop,
    libraryPicker: picker,
    referenceRecipeId: null,
    selectReferenceRecipe: noop,
    referencePicker: picker,
    aiSpec: { ingredients: '', tools: '', notes: '' },
    updateAiSpec: noop,
    canSubmit: false,
    submit: noop,
  };
}

describe('mobile layout styles', () => {
  it('lays out the summary days as an auto-fill grid from the layout token (R4)', () => {
    const days = Array.from({ length: 7 }, (_, i) => ({ day: i + 1, slots: [] }));
    const { container } = render(
      <SummaryView
        week={{ weekId: 'w', monday: '2026-08-17', sunday: '2026-08-23' }}
        summary={{ weekId: 'w', days, isEmpty: false }}
        isLoading={false}
        openDetail={noop}
        detail={null}
        closeDetail={noop}
        viewport="medium"
      />,
    );

    const grid = [...container.querySelectorAll('div')].find((el) => el.style.display === 'grid')
      .style.gridTemplateColumns;
    expect(grid).toContain('auto-fill');
    expect(grid).toContain(tokens.layout.summaryDayMin);
  });

  it('wraps the three rules rows (R5)', () => {
    render(<RulesView {...rulesProps()} />);

    const selects = [
      screen.getAllByLabelText(MESSAGES.RULES_CATEGORY_LABEL)[0],
      ...screen.getAllByLabelText(MESSAGES.RULES_DAY_LABEL),
    ];
    expect(selects).toHaveLength(3);
    selects.forEach((select) =>
      expect(select.closest('label').parentElement.style.flexWrap).toBe('wrap'),
    );
  });

  it('wraps the admin create row (R5)', () => {
    render(
      <AdminAccountsView
        accounts={[]}
        isLoading={false}
        error={null}
        actingUserId="a"
        newUsername=""
        setNewUsername={noop}
        newTemporaryPassword=""
        setNewTemporaryPassword={noop}
        canCreate={false}
        create={noop}
        confirm={confirm}
      />,
    );

    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_CREATE).parentElement.style.flexWrap).toBe(
      'wrap',
    );
  });

  it('wraps AccountRow (R5)', () => {
    const { container } = render(<AccountRow {...accountRowProps()} />);

    expect(container.querySelector('li').style.flexWrap).toBe('wrap');
  });

  it('wraps the shopping re-sync row (R5)', () => {
    render(
      <ShoppingListView
        uncheckedItems={[]}
        checkedItems={[]}
        isLoading={false}
        liveWeeks={null}
        isFormOpen={false}
        isEditing={false}
        draft={{ name: '', quantity: '', unit: '' }}
        updateDraftField={noop}
        canSaveItem={false}
        openAdd={noop}
        openEdit={noop}
        closeForm={noop}
        saveItem={noop}
        setChecked={noop}
        remove={noop}
        confirm={confirm}
        isResyncing={false}
        resync={noop}
        error={null}
      />,
    );

    expect(screen.getByText(MESSAGES.SHOPPING_LIST_RESYNC).parentElement.style.flexWrap).toBe(
      'wrap',
    );
  });

  it('wraps the AI preview action row (R5)', () => {
    const recipe = { name: 'x', category: 'meat', ingredients: [], tools: [], procedure: [] };
    render(
      <AiRecipePreview recipe={recipe} onAccept={noop} onDiscard={noop} onRegenerate={noop} />,
    );

    expect(screen.getByText(MESSAGES.AI_ACCEPT).parentElement.style.flexWrap).toBe('wrap');
  });

  it('wraps the method tabs and the ingredient row (R5)', () => {
    render(<RecipeAuthoringForm {...authoringProps()} />);

    const tabs = screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_AI).parentElement;
    const row = screen.getByText(MESSAGES.RECIPE_AUTHORING_REMOVE_INGREDIENT).parentElement;
    expect(tabs.style.flexWrap).toBe('wrap');
    expect(row.style.flexWrap).toBe('wrap');
  });

  it('sets border-box on shared and authoring inputs (R6)', () => {
    expect(inputStyle.boxSizing).toBe('border-box');
    expect(selectStyle.boxSizing).toBe('border-box');

    render(<RecipeAuthoringForm {...authoringProps()} />);
    const name = screen.getByPlaceholderText(MESSAGES.RECIPE_AUTHORING_INGREDIENT_NAME_LABEL);
    expect(name.style.boxSizing).toBe('border-box');
  });

  it('sets border-box on login and set-password inputs (R6)', () => {
    const login = render(
      <LoginView
        username=""
        setUsername={noop}
        password=""
        setPassword={noop}
        canSubmit
        submit={noop}
        error={null}
        isSubmitting={false}
      />,
    );
    login.container.querySelectorAll('input').forEach((el) => {
      expect(el.style.boxSizing).toBe('border-box');
    });
    cleanup();

    const setPw = render(
      <SetPasswordView
        status="passwordResetPending"
        newPassword=""
        setNewPassword={noop}
        confirmPassword=""
        setConfirmPassword={noop}
        mismatch={false}
        canSubmit
        submit={noop}
        cancel={noop}
        error={null}
        isSubmitting={false}
      />,
    );
    const inputs = setPw.container.querySelectorAll('input');
    expect(inputs).toHaveLength(2);
    inputs.forEach((el) => expect(el.style.boxSizing).toBe('border-box'));
  });
});

// @vitest-environment jsdom
// R7-R9: 16 px inputs, label-wrapped shopping rows, labelled authoring inputs.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { tokens } from '../../src/tokens/index.js';
import { MESSAGES } from '../../src/messages/index.js';
import { inputStyle, selectStyle } from '../../src/tokens/controlStyles.js';
import { LibraryFilters } from '../../src/components/LibraryFilters.jsx';
import { LoginView } from '../../src/components/LoginView.jsx';
import { SetPasswordView } from '../../src/components/SetPasswordView.jsx';
import { RecipeAuthoringForm } from '../../src/components/RecipeAuthoringForm.jsx';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';

afterEach(cleanup);

const noop = vi.fn();
const picker = {
  filters: { name: '', category: '' },
  setName: noop,
  setCategory: noop,
  recipes: [],
};

function authoringProps() {
  return {
    mode: 'candidate',
    methods: ['scratch'],
    method: 'scratch',
    setMethod: noop,
    form: {
      name: '',
      category: '',
      servings: '',
      estimatedTime: '',
      ingredients: [{ name: '', quantity: '', unit: '' }],
      tools: [''],
      procedure: [''],
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
    uncheckedItems: [{ id: 's-1', name: 'arroz', quantity: 500, unit: 'g', checked: false }],
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
    confirm: { pending: null, confirm: noop, cancel: noop },
    isResyncing: false,
    resync: noop,
    error: null,
    ...overrides,
  };
}

describe('input ergonomics', () => {
  it('the input font-size token is 16px and the shared control styles use it (R7)', () => {
    expect(tokens.fontSize.input).toBe('16px');
    expect(inputStyle.fontSize).toBe(tokens.fontSize.input);
    expect(selectStyle.fontSize).toBe(tokens.fontSize.input);
  });

  it('library search input and select use the input font size (R7)', () => {
    const { container } = render(
      <LibraryFilters filters={{ name: '', category: '' }} setName={noop} setCategory={noop} />,
    );

    const controls = container.querySelectorAll('input, select');
    expect(controls.length).toBeGreaterThan(1);
    controls.forEach((el) => expect(el.style.fontSize).toBe(tokens.fontSize.input));
  });

  it('authoring, login and set-password inputs use the input font size (R7)', () => {
    const authoring = render(<RecipeAuthoringForm {...authoringProps()} />);
    authoring.container.querySelectorAll('input, select').forEach((el) => {
      expect(el.style.fontSize).toBe(tokens.fontSize.input);
    });
    cleanup();

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
      expect(el.style.fontSize).toBe(tokens.fontSize.input);
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
    setPw.container.querySelectorAll('input').forEach((el) => {
      expect(el.style.fontSize).toBe(tokens.fontSize.input);
    });
  });

  it('clicking the item text toggles its checkbox (R8)', () => {
    const setChecked = vi.fn();
    render(<ShoppingListView {...shoppingProps({ setChecked })} />);

    fireEvent.click(screen.getByText(/arroz · 500 g/));

    expect(setChecked).toHaveBeenCalledWith(expect.objectContaining({ id: 's-1' }), true);
  });

  it('authoring inputs are reachable by label text (R9)', () => {
    render(<RecipeAuthoringForm {...authoringProps()} />);

    expect(screen.getByLabelText(MESSAGES.RECIPE_AUTHORING_INGREDIENT_NAME_LABEL)).not.toBeNull();
    expect(
      screen.getByLabelText(MESSAGES.RECIPE_AUTHORING_INGREDIENT_QUANTITY_LABEL),
    ).not.toBeNull();
    expect(screen.getByLabelText(MESSAGES.RECIPE_AUTHORING_TOOL_LABEL)).not.toBeNull();
    expect(screen.getByLabelText(MESSAGES.RECIPE_AUTHORING_STEP_LABEL)).not.toBeNull();
  });
});

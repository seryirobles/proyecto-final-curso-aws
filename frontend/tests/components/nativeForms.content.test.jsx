// @vitest-environment jsdom
// R22-R25, R27: native forms on shopping, rules and recipe authoring.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, fireEvent, cleanup } from '@testing-library/react';
import { RulesView } from '../../src/components/RulesView.jsx';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';
import { RecipeAuthoringForm } from '../../src/components/RecipeAuthoringForm.jsx';

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

// Every button inside a form must be an explicit non-submit, except submit ones.
function expectNoStrayButtons(form) {
  form.querySelectorAll('button').forEach((button) => {
    expect(['button', 'submit']).toContain(button.getAttribute('type'));
  });
}

function shoppingProps(overrides = {}) {
  return {
    uncheckedItems: [],
    checkedItems: [],
    isLoading: false,
    liveWeeks: null,
    isFormOpen: true,
    isEditing: false,
    draft: { name: 'arroz', quantity: '1', unit: 'g' },
    updateDraftField: noop,
    canSaveItem: true,
    openAdd: noop,
    openEdit: noop,
    closeForm: noop,
    saveItem: vi.fn(),
    setChecked: noop,
    remove: noop,
    confirm,
    isResyncing: false,
    resync: noop,
    error: null,
    ...overrides,
  };
}

function rulesProps(overrides = {}) {
  return {
    categoryCounts: [{ type: 'categoryCount', category: 'meat', count: 2 }],
    pins: [],
    disabledDays: [{ type: 'disabledDay', day: 2 }],
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
    saveCategoryCount: vi.fn(),
    pinDraft: { day: '', slot: '' },
    pinDayOptions: [],
    setPinDay: noop,
    setPinSlot: noop,
    pinRecipeId: null,
    selectPinRecipe: noop,
    canSavePin: true,
    savePin: vi.fn(),
    disabledDayDraft: { day: '' },
    disabledDayOptions: [],
    setDisabledDayDay: noop,
    canSaveDisabledDay: true,
    saveDisabledDay: vi.fn(),
    ...overrides,
  };
}

function authoringProps(overrides = {}) {
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
      tools: ['olla'],
      procedure: ['paso'],
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
    canSubmit: true,
    submit: vi.fn(),
    ...overrides,
  };
}

describe('shopping item form', () => {
  it('submits through the form and ignores it when disabled (R22, R25)', () => {
    const saveItem = vi.fn();
    const { container, rerender } = render(<ShoppingListView {...shoppingProps({ saveItem })} />);

    fireEvent.submit(container.querySelector('form'));
    expect(saveItem).toHaveBeenCalledTimes(1);
    expectNoStrayButtons(container.querySelector('form'));

    rerender(<ShoppingListView {...shoppingProps({ saveItem, canSaveItem: false })} />);
    fireEvent.submit(container.querySelector('form'));
    expect(saveItem).toHaveBeenCalledTimes(1);
  });
});

describe('rules forms', () => {
  it('each of the three forms submits its own save handler (R23)', () => {
    const props = rulesProps();
    const { container } = render(<RulesView {...props} />);

    const forms = container.querySelectorAll('form');
    expect(forms).toHaveLength(3);
    fireEvent.submit(forms[0]);
    fireEvent.submit(forms[1]);
    fireEvent.submit(forms[2]);

    expect(props.saveCategoryCount).toHaveBeenCalledTimes(1);
    expect(props.savePin).toHaveBeenCalledTimes(1);
    expect(props.saveDisabledDay).toHaveBeenCalledTimes(1);
    forms.forEach(expectNoStrayButtons);
  });

  it('ignores a submit while that form is disabled (R25)', () => {
    const props = rulesProps({
      canSaveCategoryCount: false,
      canSavePin: false,
      canSaveDisabledDay: false,
    });
    const { container } = render(<RulesView {...props} />);

    container.querySelectorAll('form').forEach((form) => fireEvent.submit(form));

    expect(props.saveCategoryCount).not.toHaveBeenCalled();
    expect(props.savePin).not.toHaveBeenCalled();
    expect(props.saveDisabledDay).not.toHaveBeenCalled();
  });
});

describe('recipe authoring form', () => {
  it('scratch and library methods submit through the form (R24)', () => {
    for (const method of ['scratch', 'library']) {
      const props = authoringProps({ method, submit: vi.fn() });
      const { container } = render(<RecipeAuthoringForm {...props} />);

      fireEvent.submit(container.querySelector('form'));

      expect(props.submit).toHaveBeenCalledTimes(1);
      cleanup();
    }
  });

  it('ignores a submit while disabled (R25)', () => {
    const props = authoringProps({ canSubmit: false });
    const { container } = render(<RecipeAuthoringForm {...props} />);

    fireEvent.submit(container.querySelector('form'));

    expect(props.submit).not.toHaveBeenCalled();
  });

  it('every non-submit button in the form is type=button, in all methods (R27)', () => {
    for (const method of ['scratch', 'library', 'ai']) {
      const { container } = render(<RecipeAuthoringForm {...authoringProps({ method })} />);

      const form = container.querySelector('form');
      expect(form).not.toBeNull();
      expectNoStrayButtons(form);
      cleanup();
    }
  });
});

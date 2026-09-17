// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { RecipeAuthoringForm } from '../../src/components/RecipeAuthoringForm.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

function pickerProps() {
  return {
    filters: { name: '', category: '' },
    setName: vi.fn(),
    setCategory: vi.fn(),
    recipes: [],
  };
}

function baseProps(overrides = {}) {
  return {
    mode: 'candidate',
    methods: ['library', 'scratch', 'ai'],
    method: 'scratch',
    setMethod: vi.fn(),
    form: {
      name: '',
      category: '',
      servings: '',
      estimatedTime: '',
      ingredients: [],
      tools: [],
      procedure: [],
    },
    updateField: vi.fn(),
    addIngredient: vi.fn(),
    updateIngredient: vi.fn(),
    removeIngredient: vi.fn(),
    addTool: vi.fn(),
    updateTool: vi.fn(),
    removeTool: vi.fn(),
    addProcedureStep: vi.fn(),
    updateProcedureStep: vi.fn(),
    removeProcedureStep: vi.fn(),
    libraryRecipeId: null,
    selectLibraryRecipe: vi.fn(),
    libraryPicker: pickerProps(),
    referenceRecipeId: null,
    selectReferenceRecipe: vi.fn(),
    referencePicker: pickerProps(),
    aiSpec: { ingredients: '', tools: '', notes: '' },
    updateAiSpec: vi.fn(),
    canSubmit: false,
    submit: vi.fn(),
    ...overrides,
  };
}

describe('RecipeAuthoringForm', () => {
  it('renders a tab per method, in order', () => {
    render(<RecipeAuthoringForm {...baseProps()} />);

    const tabs = screen
      .getAllByRole('button')
      .slice(0, 3)
      .map((btn) => btn.textContent);
    expect(tabs).toEqual([
      MESSAGES.RECIPE_AUTHORING_METHOD_LIBRARY,
      MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH,
      MESSAGES.RECIPE_AUTHORING_METHOD_AI,
    ]);
  });

  it('clicking a tab calls setMethod with that method', () => {
    const setMethod = vi.fn();
    render(<RecipeAuthoringForm {...baseProps({ setMethod })} />);

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_METHOD_AI));

    expect(setMethod).toHaveBeenCalledWith('ai');
  });

  it('renders the manual-form fields for the scratch method (category off CATEGORY_LABELS)', () => {
    render(<RecipeAuthoringForm {...baseProps({ method: 'scratch' })} />);

    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_NAME_LABEL)).not.toBeNull();
    expect(screen.getByText('Carne')).not.toBeNull(); // CATEGORY_LABELS.meat
    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_ADD_INGREDIENT)).not.toBeNull();
  });

  it('renders an ingredient row with a unit dropdown off UNIT_LABELS', () => {
    const form = {
      name: '',
      category: '',
      servings: '',
      estimatedTime: '',
      ingredients: [{ name: 'lentejas', quantity: '300', unit: 'g' }],
      tools: [],
      procedure: [],
    };
    render(<RecipeAuthoringForm {...baseProps({ method: 'scratch', form })} />);

    expect(screen.getByDisplayValue('lentejas')).not.toBeNull();
    expect(screen.getByText('g')).not.toBeNull(); // UNIT_LABELS.g
  });

  it('does not render the library or scratch content on the ai tab, only the disabled notice', () => {
    render(<RecipeAuthoringForm {...baseProps({ method: 'ai' })} />);

    expect(screen.getByText(MESSAGES.AI_GENERATION_UNAVAILABLE)).not.toBeNull();
    expect(screen.queryByText(MESSAGES.RECIPE_AUTHORING_NAME_LABEL)).toBeNull();
  });

  it('renders the reference-recipe picker on the ai tab (T27, design.md section 1.3 stub)', () => {
    render(<RecipeAuthoringForm {...baseProps({ method: 'ai' })} />);

    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_REFERENCE_RECIPE_LABEL)).not.toBeNull();
    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_NAME_LABEL)).not.toBeNull();
  });

  it('the ai tab submit control is disabled (design.md section 1.3)', () => {
    render(<RecipeAuthoringForm {...baseProps({ method: 'ai' })} />);

    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT).closest('button').disabled).toBe(
      true,
    );
  });

  it('renders LibraryRecipePicker on the library tab (T27)', () => {
    render(<RecipeAuthoringForm {...baseProps({ method: 'library' })} />);

    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_NAME_LABEL)).not.toBeNull();
  });

  it('the library tab has a submit control, enabled once a recipe is selected (F5)', () => {
    const submit = vi.fn();
    const { rerender } = render(
      <RecipeAuthoringForm {...baseProps({ method: 'library', canSubmit: false, submit })} />,
    );

    const disabledButton = screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT).closest('button');
    expect(disabledButton.disabled).toBe(true);

    rerender(
      <RecipeAuthoringForm {...baseProps({ method: 'library', canSubmit: true, submit })} />,
    );

    const enabledButton = screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT).closest('button');
    expect(enabledButton.disabled).toBe(false);
    fireEvent.click(enabledButton);
    expect(submit).toHaveBeenCalledTimes(1);
  });

  it('mode "library" never renders a library tab (R8)', () => {
    render(<RecipeAuthoringForm {...baseProps({ mode: 'library', methods: ['scratch', 'ai'] })} />);

    expect(screen.queryByText(MESSAGES.RECIPE_AUTHORING_METHOD_LIBRARY)).toBeNull();
  });

  it('the submit button is disabled while canSubmit is false', () => {
    render(<RecipeAuthoringForm {...baseProps({ method: 'scratch', canSubmit: false })} />);

    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT).closest('button').disabled).toBe(
      true,
    );
  });

  it('clicking submit calls submit when canSubmit is true', () => {
    const submit = vi.fn();
    render(<RecipeAuthoringForm {...baseProps({ method: 'scratch', canSubmit: true, submit })} />);

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT));

    expect(submit).toHaveBeenCalledTimes(1);
  });

  // T88 guard: AiStubFields hardcodes `disabled` regardless of canSubmit
  // (T22, design.md section 1.3) - `canSubmit: true` here still must not
  // enable it, protecting the stub from a future T87-style restyle regression.
  it('the ai tab stub submit stays disabled even when canSubmit is true (T88)', () => {
    render(<RecipeAuthoringForm {...baseProps({ method: 'ai', canSubmit: true })} />);

    expect(screen.getByText(MESSAGES.RECIPE_AUTHORING_SUBMIT).closest('button').disabled).toBe(
      true,
    );
  });
});

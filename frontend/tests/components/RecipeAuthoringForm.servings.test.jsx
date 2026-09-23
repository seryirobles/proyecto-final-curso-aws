// @vitest-environment jsdom
// Issue 4 (E3-E6): the Comensales control is numeric, no upper bound. Lower
// bound moved to RecipeAuthoringForm.servingsBound.test.jsx (issue negative-
// ingredient-quantity); estimated time moved to .estimatedTime.test.jsx (G-90).
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

function fieldInput(labelText) {
  return screen.getByText(labelText).closest('label').querySelector('input');
}

describe('RecipeAuthoringForm - servings and estimated time controls', () => {
  it('renders Comensales as a numeric control stepping by one (E3)', () => {
    render(<RecipeAuthoringForm {...baseProps()} />);

    const input = fieldInput(MESSAGES.RECIPE_AUTHORING_SERVINGS_LABEL);

    expect(input.getAttribute('type')).toBe('number');
    // An absent `step` is the HTML default of 1 - either form is the stepper
    // the report asks for; anything else is not.
    expect(input.getAttribute('step') ?? '1').toBe('1');
  });

  it('bounds Comensales with no max (E4; min="0" is issue negative-ingredient-quantity E12)', () => {
    render(<RecipeAuthoringForm {...baseProps()} />);

    const input = fieldInput(MESSAGES.RECIPE_AUTHORING_SERVINGS_LABEL);

    expect(input.getAttribute('max')).toBeNull();
  });

  it('keeps Comensales a controlled field reporting its value (E3)', () => {
    const updateField = vi.fn();
    const form = { ...baseProps().form, servings: '4' };
    render(<RecipeAuthoringForm {...baseProps({ form, updateField })} />);

    const input = fieldInput(MESSAGES.RECIPE_AUTHORING_SERVINGS_LABEL);
    expect(input.value).toBe('4');

    fireEvent.change(input, { target: { value: '6' } });

    expect(updateField).toHaveBeenCalledWith('servings', '6');
  });
});

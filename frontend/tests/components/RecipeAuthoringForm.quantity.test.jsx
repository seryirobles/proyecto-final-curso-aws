// @vitest-environment jsdom
// Issue 7 (negative-ingredient-quantity), E5 and E6: the ingredient-quantity
// field warns in es-ES while it holds a non-positive value, and its native
// stepper cannot go below zero.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
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

function baseProps(quantity) {
  return {
    mode: 'library',
    methods: ['scratch', 'ai'],
    method: 'scratch',
    setMethod: vi.fn(),
    form: {
      name: 'Lentejas al curry',
      category: 'legume',
      servings: '',
      estimatedTime: '',
      ingredients: [{ name: 'lentejas', quantity, unit: 'g' }],
      tools: ['olla'],
      procedure: ['Cocer las lentejas.'],
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
  };
}

// The warning text comes from the es-ES messages module, never a literal
// (docs/conventions.md, "Castilian Spanish"), so its key must exist.
function warnings() {
  expect(typeof MESSAGES.RECIPE_AUTHORING_INVALID_QUANTITY).toBe('string');
  return screen.queryAllByText(MESSAGES.RECIPE_AUTHORING_INVALID_QUANTITY);
}

function quantityInput() {
  return screen.getByPlaceholderText(MESSAGES.RECIPE_AUTHORING_INGREDIENT_QUANTITY_LABEL);
}

describe('RecipeAuthoringForm - ingredient quantity warning', () => {
  it.each(['-300', '-0.5', '0'])('warns in es-ES while the quantity is %s (E5)', (quantity) => {
    render(<RecipeAuthoringForm {...baseProps(quantity)} />);

    expect(warnings()).toHaveLength(1);
  });

  it('shows no warning for a positive quantity (E5)', () => {
    render(<RecipeAuthoringForm {...baseProps('300')} />);

    expect(warnings()).toHaveLength(0);
  });

  it('shows no warning while the quantity field is empty - issue 5 owns that message (E5)', () => {
    render(<RecipeAuthoringForm {...baseProps('')} />);

    expect(warnings()).toHaveLength(0);
  });

  it('bounds the quantity stepper at zero, so it never steps negative (E6)', () => {
    render(<RecipeAuthoringForm {...baseProps('1')} />);

    const input = quantityInput();

    expect(input.getAttribute('type')).toBe('number');
    expect(input.getAttribute('min')).toBe('0');
  });
});

// @vitest-environment jsdom
// Issue 7 (negative-ingredient-quantity), servings extension, E11 and E12:
// Comensales warns in es-ES while it holds a non-positive value, and its
// native stepper cannot go below zero.
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

function baseProps(servings) {
  return {
    mode: 'library',
    methods: ['scratch', 'ai'],
    method: 'scratch',
    setMethod: vi.fn(),
    form: {
      name: 'Lentejas al curry',
      category: 'legume',
      servings,
      estimatedTime: '',
      ingredients: [{ name: 'lentejas', quantity: '300', unit: 'g' }],
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

// The text must come from the es-ES messages module, never a literal.
function warnings() {
  expect(typeof MESSAGES.RECIPE_AUTHORING_INVALID_SERVINGS).toBe('string');
  return screen.queryAllByText(MESSAGES.RECIPE_AUTHORING_INVALID_SERVINGS);
}

function servingsInput() {
  return screen
    .getByText(MESSAGES.RECIPE_AUTHORING_SERVINGS_LABEL)
    .closest('label')
    .querySelector('input');
}

describe('RecipeAuthoringForm - servings bound', () => {
  it.each(['-4', '-1', '0'])('warns in es-ES while servings is %s (E11)', (servings) => {
    render(<RecipeAuthoringForm {...baseProps(servings)} />);

    expect(warnings()).toHaveLength(1);
  });

  it.each(['4', ''])('shows no warning while servings is "%s" (E11)', (servings) => {
    render(<RecipeAuthoringForm {...baseProps(servings)} />);

    expect(warnings()).toHaveLength(0);
  });

  it('bounds the servings stepper at zero, so it never steps negative (E12)', () => {
    render(<RecipeAuthoringForm {...baseProps('1')} />);

    const input = servingsInput();

    expect(input.getAttribute('type')).toBe('number');
    expect(input.getAttribute('min')).toBe('0');
  });
});

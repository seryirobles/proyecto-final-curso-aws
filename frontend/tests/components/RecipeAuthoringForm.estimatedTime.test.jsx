// @vitest-environment jsdom
// Issue 11 (E3, E4, E8): Tiempo estimado is a numeric minute control bounded
// at 0 and 6000, not the free-text box G-85 called for - G-90 supersedes that
// part of G-85. The two G-85 cases in RecipeAuthoringForm.servings.test.jsx
// are replaced by these; Comensales is untouched (issue 4).
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

describe('RecipeAuthoringForm - Tiempo estimado as a minute count', () => {
  it('renders Tiempo estimado as a numeric control stepping by one (E3)', () => {
    render(<RecipeAuthoringForm {...baseProps()} />);

    const input = fieldInput(MESSAGES.RECIPE_AUTHORING_ESTIMATED_TIME_LABEL);

    expect(input.getAttribute('type')).toBe('number');
    // An absent `step` is the HTML default of 1 - either form is a whole-minute
    // stepper; anything else is not.
    expect(input.getAttribute('step') ?? '1').toBe('1');
  });

  it('bounds Tiempo estimado at 0 and 6000 minutes (E3, E8, G-90)', () => {
    render(<RecipeAuthoringForm {...baseProps()} />);

    const input = fieldInput(MESSAGES.RECIPE_AUTHORING_ESTIMATED_TIME_LABEL);

    expect(input.getAttribute('min')).toBe('0');
    expect(input.getAttribute('max')).toBe('6000');
  });

  it('keeps Tiempo estimado a controlled field reporting its value (E3)', () => {
    const updateField = vi.fn();
    const form = { ...baseProps().form, estimatedTime: '45' };
    render(<RecipeAuthoringForm {...baseProps({ form, updateField })} />);

    const input = fieldInput(MESSAGES.RECIPE_AUTHORING_ESTIMATED_TIME_LABEL);
    expect(input.value).toBe('45');

    fireEvent.change(input, { target: { value: '90' } });

    expect(updateField).toHaveBeenCalledWith('estimatedTime', '90');
  });

  it('names the unit in the Tiempo estimado label, since the value no longer carries it (E4)', () => {
    expect(MESSAGES.RECIPE_AUTHORING_ESTIMATED_TIME_LABEL.toLowerCase()).toContain('minutos');
    expect(MESSAGES.RECIPE_DETAIL_ESTIMATED_TIME.toLowerCase()).toContain('minutos');
  });
});

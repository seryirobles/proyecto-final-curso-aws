// @vitest-environment jsdom
// Issue recipe-saved-without-required-sections, E8 (scope extension): an
// empty ingredients / tools / procedure section warns in es-ES beside it,
// so the disabled "Guardar receta" is never unexplained.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { RecipeAuthoringForm } from '../../src/components/RecipeAuthoringForm.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

const FILLED = {
  ingredients: [{ name: 'lentejas', quantity: '300', unit: 'g' }],
  tools: ['olla'],
  procedure: ['Cocer las lentejas.'],
};

// section -> [its warning key, its heading, the heading that follows it]
const SECTIONS = {
  ingredients: [
    'RECIPE_AUTHORING_MISSING_INGREDIENTS',
    MESSAGES.RECIPE_AUTHORING_INGREDIENTS_LABEL,
    MESSAGES.RECIPE_AUTHORING_TOOLS_LABEL,
  ],
  tools: [
    'RECIPE_AUTHORING_MISSING_TOOLS',
    MESSAGES.RECIPE_AUTHORING_TOOLS_LABEL,
    MESSAGES.RECIPE_AUTHORING_PROCEDURE_LABEL,
  ],
  procedure: [
    'RECIPE_AUTHORING_MISSING_PROCEDURE',
    MESSAGES.RECIPE_AUTHORING_PROCEDURE_LABEL,
    null,
  ],
};

function pickerProps() {
  return {
    filters: { name: '', category: '' },
    setName: vi.fn(),
    setCategory: vi.fn(),
    recipes: [],
  };
}

function baseProps(sections, method = 'scratch') {
  return {
    mode: 'library',
    methods: ['library', 'scratch', 'ai'],
    method,
    setMethod: vi.fn(),
    form: {
      name: 'Lentejas al curry',
      category: 'legume',
      servings: '',
      estimatedTime: '',
      ...sections,
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

// Text comes from the es-ES messages module, never a literal
// (docs/conventions.md, "Castilian Spanish"), so each key must exist.
function warningsFor(key) {
  expect(typeof MESSAGES[key]).toBe('string');
  return screen.queryAllByText(MESSAGES[key]);
}

function follows(node, reference) {
  return Boolean(reference.compareDocumentPosition(node) & reference.DOCUMENT_POSITION_FOLLOWING);
}

describe('RecipeAuthoringForm - empty required section warning', () => {
  it.each(Object.keys(SECTIONS))('warns in es-ES beside an empty %s section (E8)', (section) => {
    render(<RecipeAuthoringForm {...baseProps({ ...FILLED, [section]: [] })} />);
    const [key, heading, nextHeading] = SECTIONS[section];

    const shown = warningsFor(key);
    expect(shown).toHaveLength(1);
    expect(follows(shown[0], screen.getByText(heading, { selector: 'h3' }))).toBe(true);
    if (nextHeading) {
      const next = screen.getByText(nextHeading, { selector: 'h3' });
      expect(follows(next, shown[0])).toBe(true);
    }
    for (const [other, [otherKey]] of Object.entries(SECTIONS)) {
      if (other !== section) expect(warningsFor(otherKey)).toHaveLength(0);
    }
  });

  it('warns once per section when all three are empty (E8)', () => {
    render(<RecipeAuthoringForm {...baseProps({ ingredients: [], tools: [], procedure: [] })} />);

    for (const [key] of Object.values(SECTIONS)) {
      expect(warningsFor(key)).toHaveLength(1);
    }
  });

  it('shows no section warning on a recipe with one item in each section (E8, E7)', () => {
    render(<RecipeAuthoringForm {...baseProps(FILLED)} />);

    for (const [key] of Object.values(SECTIONS)) {
      expect(warningsFor(key)).toHaveLength(0);
    }
  });

  it('shows no section warning on the library-pick method (E8)', () => {
    render(
      <RecipeAuthoringForm
        {...baseProps({ ingredients: [], tools: [], procedure: [] }, 'library')}
      />,
    );

    for (const [key] of Object.values(SECTIONS)) {
      expect(warningsFor(key)).toHaveLength(0);
    }
  });
});

// @vitest-environment jsdom
// Issue close-button-style (E4-E5, scope extension): the week view's
// "Añadir plato" panel's "Cerrar" must carry the same shared secondary-button
// treatment as the library authoring panel's (E1).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';

vi.mock('../../src/hooks/useRecipeAuthoring.js', () => ({
  useRecipeAuthoring: vi.fn(),
}));

import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';
import { CandidateAuthoring } from '../../src/components/CandidateAuthoring.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { secondaryButtonStyle } from '../../src/tokens/controlStyles.js';

afterEach(cleanup);

// Same treatment properties as LibraryView.closeButton.test.jsx; extra
// decoration (margins) is deliberately not asserted.
const TREATMENT = [
  'backgroundColor',
  'color',
  'borderStyle',
  'borderWidth',
  'borderColor',
  'borderRadius',
  'padding',
  'fontWeight',
];

function treatmentOf(style) {
  return Object.fromEntries(TREATMENT.map((property) => [property, style[property]]));
}

function sharedSecondaryTreatment() {
  const probe = document.createElement('button');
  Object.assign(probe.style, secondaryButtonStyle);
  return treatmentOf(probe.style);
}

function pickerProps() {
  return {
    filters: { name: '', category: '' },
    setName: vi.fn(),
    setCategory: vi.fn(),
    recipes: [],
  };
}

function authoringProps() {
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
  };
}

function closeControl() {
  return screen.getByText(MESSAGES.RECIPE_DETAIL_CLOSE).closest('button');
}

describe('CandidateAuthoring close control', () => {
  it('carries the shared secondary-button treatment (E4)', () => {
    useRecipeAuthoring.mockReturnValue(authoringProps());
    render(<CandidateAuthoring onSubmit={vi.fn()} onClose={vi.fn()} />);

    expect(treatmentOf(closeControl().style)).toEqual(sharedSecondaryTreatment());
  });

  it('still calls onClose when clicked (E5)', () => {
    useRecipeAuthoring.mockReturnValue(authoringProps());
    const onClose = vi.fn();
    render(<CandidateAuthoring onSubmit={vi.fn()} onClose={onClose} />);

    fireEvent.click(closeControl());

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

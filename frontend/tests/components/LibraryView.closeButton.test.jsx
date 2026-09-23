// @vitest-environment jsdom
// Issue close-button-style (E1-E3): the authoring panel's "Cerrar" control
// must carry the shared secondary-button treatment, like every other
// dismiss-the-open-form button (ShoppingListView's "Cancelar").
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { LibraryView } from '../../src/components/LibraryView.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { secondaryButtonStyle } from '../../src/tokens/controlStyles.js';

afterEach(cleanup);

// The properties that make up a button's visual treatment here. Extra
// decoration (icon layout, margins) is deliberately not asserted.
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

// Resolved off the token module itself, so the assertion is about the
// treatment the app defines, not about how a component imports it.
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
    mode: 'library',
    methods: ['scratch', 'ai'],
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

function baseProps(overrides = {}) {
  return {
    recipes: [],
    filters: { name: '', category: '' },
    setName: vi.fn(),
    setCategory: vi.fn(),
    isLoading: false,
    isAuthoringOpen: true,
    authoring: authoringProps(),
    openAdd: vi.fn(),
    openEdit: vi.fn(),
    closeAuthoring: vi.fn(),
    remove: vi.fn(),
    confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
    openDetail: vi.fn(),
    detail: null,
    detailError: null,
    closeDetail: vi.fn(),
    error: null,
    ...overrides,
  };
}

function closeControl() {
  return screen.getByText(MESSAGES.RECIPE_DETAIL_CLOSE).closest('button');
}

describe('LibraryView authoring-panel close control', () => {
  it('carries the shared secondary-button treatment (E1)', () => {
    render(<LibraryView {...baseProps()} />);

    expect(treatmentOf(closeControl().style)).toEqual(sharedSecondaryTreatment());
  });

  it('leaves no button unstyled while the authoring panel is open (E2)', () => {
    render(<LibraryView {...baseProps()} />);

    const unstyled = screen
      .getAllByRole('button')
      .filter((button) => button.style.length === 0)
      .map((button) => button.textContent);

    expect(unstyled).toEqual([]);
  });

  it('still calls closeAuthoring when clicked (E3)', () => {
    const closeAuthoring = vi.fn();
    render(<LibraryView {...baseProps({ closeAuthoring })} />);

    fireEvent.click(closeControl());

    expect(closeAuthoring).toHaveBeenCalledTimes(1);
  });
});

// @vitest-environment jsdom
// R10-R14: titled authoring forms that scroll into view once per open target.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';

vi.mock('../../src/hooks/useRecipeAuthoring.js', () => ({ useRecipeAuthoring: vi.fn() }));

import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';
import { CandidateAuthoring } from '../../src/components/CandidateAuthoring.jsx';
import { LibraryView } from '../../src/components/LibraryView.jsx';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

const noop = vi.fn();
const picker = {
  filters: { name: '', category: '' },
  setName: noop,
  setCategory: noop,
  recipes: [],
};
const authoring = {
  mode: 'candidate',
  methods: ['scratch'],
  method: 'scratch',
  setMethod: noop,
  form: {
    name: '',
    category: '',
    servings: '',
    estimatedTime: '',
    ingredients: [],
    tools: [],
    procedure: [],
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

let scrollIntoView;
beforeEach(() => {
  scrollIntoView = vi.fn();
  window.Element.prototype.scrollIntoView = scrollIntoView;
  useRecipeAuthoring.mockReturnValue(authoring);
});
afterEach(() => {
  cleanup();
  delete window.Element.prototype.scrollIntoView;
});

function libraryProps(overrides = {}) {
  return {
    recipes: [],
    filters: { name: '', category: '' },
    setName: noop,
    setCategory: noop,
    isLoading: false,
    isAuthoringOpen: true,
    isEditing: false,
    authoring,
    openAdd: noop,
    openEdit: noop,
    closeAuthoring: noop,
    remove: noop,
    confirm: { pending: null, confirm: noop, cancel: noop },
    openDetail: noop,
    detail: null,
    detailError: null,
    closeDetail: noop,
    error: null,
    ...overrides,
  };
}

function shoppingProps(overrides = {}) {
  return {
    uncheckedItems: [],
    checkedItems: [],
    isLoading: false,
    liveWeeks: null,
    isFormOpen: true,
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

describe('add/edit forms open in view', () => {
  it('Week add: titled with day and slot, scrolled once (R10, R11)', () => {
    render(
      <CandidateAuthoring
        target={{ weekId: 'w', day: 1, slot: 1 }}
        onSubmit={noop}
        onClose={noop}
      />,
    );

    expect(screen.getByText(MESSAGES.ADD_CANDIDATE_TITLE('lunes', 'Comida'))).not.toBeNull();
    expect(MESSAGES.ADD_CANDIDATE_TITLE('lunes', 'Comida')).toBe('Añadir a lunes · Comida');
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
  });

  it('Week edit: titled "Editar · lunes · Comida" (R11)', () => {
    render(
      <CandidateAuthoring
        target={{ weekId: 'w', day: 1, slot: 1, candidateId: 'c1' }}
        initialRecipe={{}}
        onSubmit={noop}
        onClose={noop}
      />,
    );

    expect(screen.getByText('Editar · lunes · Comida')).not.toBeNull();
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
  });

  it('Week: a re-render with an equal rebuilt target does not scroll again (R14)', () => {
    const { rerender } = render(
      <CandidateAuthoring
        target={{ weekId: 'w', day: 1, slot: 1 }}
        onSubmit={noop}
        onClose={noop}
      />,
    );

    rerender(
      <CandidateAuthoring
        target={{ weekId: 'w', day: 1, slot: 1 }}
        onSubmit={noop}
        onClose={noop}
      />,
    );

    expect(scrollIntoView).toHaveBeenCalledTimes(1);
  });

  it('Library: "Nueva receta" / "Editar receta", scrolled once (R10, R12, R14)', () => {
    const { rerender } = render(<LibraryView {...libraryProps()} />);
    expect(screen.getByText('Nueva receta')).not.toBeNull();
    expect(scrollIntoView).toHaveBeenCalledTimes(1);

    rerender(<LibraryView {...libraryProps({ recipes: [] })} />);
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
    cleanup();

    render(<LibraryView {...libraryProps({ isEditing: true })} />);
    expect(screen.getByText('Editar receta')).not.toBeNull();
  });

  it('Shopping: "Añadir elemento" / "Editar elemento" form titles, scrolled (R10, R13)', () => {
    render(<ShoppingListView {...shoppingProps()} />);
    expect(screen.getAllByText('Añadir elemento').length).toBeGreaterThanOrEqual(2);
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
    cleanup();

    render(<ShoppingListView {...shoppingProps({ isEditing: true })} />);
    expect(screen.getByText('Editar elemento', { selector: 'h3' })).not.toBeNull();
  });
});

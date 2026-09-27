// @vitest-environment jsdom
// T31 (R11, R12, R13): search/category/result list, and the same
// component/props shape reaching all 3 R12 call sites (T27, T33) -
// see progress/impl_frontend_spa.md, "Rules view (T32-T34)".
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { LibraryRecipePicker } from '../../src/components/LibraryRecipePicker.jsx';
import { RecipeAuthoringForm } from '../../src/components/RecipeAuthoringForm.jsx';
import { RulesView } from '../../src/components/RulesView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

const RECIPE_A = { id: 'r-1', name: 'Lentejas al curry', category: 'legume', author: 'Marta' };
const RECIPE_B = { id: 'r-2', name: 'Tortilla', category: 'eggs', author: 'Diego' };

function baseProps(overrides = {}) {
  return {
    filters: { name: '', category: '' },
    setName: vi.fn(),
    setCategory: vi.fn(),
    recipes: [RECIPE_A, RECIPE_B],
    selectedRecipeId: null,
    onSelect: vi.fn(),
    ...overrides,
  };
}

describe('LibraryRecipePicker', () => {
  it('renders a search-by-name input (R11)', () => {
    render(<LibraryRecipePicker {...baseProps()} />);

    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_NAME_LABEL)).not.toBeNull();
  });

  it('typing in the search input calls setName (R11)', () => {
    const setName = vi.fn();
    render(<LibraryRecipePicker {...baseProps({ setName })} />);

    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'lentejas' } });

    expect(setName).toHaveBeenCalledWith('lentejas');
  });

  it('renders a category select with every CATEGORY_LABELS option (R13)', () => {
    render(<LibraryRecipePicker {...baseProps()} />);

    expect(screen.getByText('Legumbres')).not.toBeNull();
    expect(screen.getByText('Huevos')).not.toBeNull();
  });

  it('renders every recipe in the result list', () => {
    render(<LibraryRecipePicker {...baseProps()} />);

    expect(screen.getByText('Lentejas al curry')).not.toBeNull();
    expect(screen.getByText('Tortilla')).not.toBeNull();
  });

  it('clicking a result calls onSelect with that recipe id', () => {
    const onSelect = vi.fn();
    render(<LibraryRecipePicker {...baseProps({ onSelect })} />);

    fireEvent.click(screen.getAllByText(MESSAGES.LIBRARY_PICKER_SELECT)[1]);

    expect(onSelect).toHaveBeenCalledWith('r-2');
  });

  it('shows the selected state on the matching card only (selectedRecipeId)', () => {
    render(<LibraryRecipePicker {...baseProps({ selectedRecipeId: 'r-2' })} />);

    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_SELECTED)).not.toBeNull();
    expect(screen.getAllByText(MESSAGES.LIBRARY_PICKER_SELECT)).toHaveLength(1);
  });

  it('renders EmptyState guidance when no recipe matches the filters', () => {
    render(<LibraryRecipePicker {...baseProps({ recipes: [] })} />);

    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_EMPTY)).not.toBeNull();
  });

  it('reaches RecipeAuthoringForm library tab with the same component/props shape (T27)', () => {
    const formProps = {
      mode: 'candidate',
      methods: ['library', 'scratch', 'ai'],
      method: 'library',
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
      libraryRecipeId: null,
      selectLibraryRecipe: vi.fn(),
      libraryPicker: baseProps(),
      referenceRecipeId: null,
      selectReferenceRecipe: vi.fn(),
      referencePicker: baseProps({ recipes: [] }),
      aiSpec: { ingredients: '', tools: '', notes: '' },
      updateAiSpec: vi.fn(),
      canSubmit: false,
      submit: vi.fn(),
    };
    render(<RecipeAuthoringForm {...formProps} />);

    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_NAME_LABEL)).not.toBeNull();
    expect(screen.getByText('Lentejas al curry')).not.toBeNull();
  });

  it('reaches RecipeAuthoringForm ai reference-recipe field with the same component/props shape (T27)', () => {
    const formProps = {
      mode: 'candidate',
      methods: ['library', 'scratch', 'ai'],
      method: 'ai',
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
      libraryRecipeId: null,
      selectLibraryRecipe: vi.fn(),
      libraryPicker: baseProps({ recipes: [] }),
      referenceRecipeId: null,
      selectReferenceRecipe: vi.fn(),
      referencePicker: baseProps(),
      aiSpec: { ingredients: '', tools: '', notes: '' },
      updateAiSpec: vi.fn(),
      canSubmit: false,
      submit: vi.fn(),
    };
    render(<RecipeAuthoringForm {...formProps} />);

    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_NAME_LABEL)).not.toBeNull();
    expect(screen.getByText('Tortilla')).not.toBeNull();
  });

  it('reaches RulesView pin field with the same component/props shape (T33, 3rd of 3 sites)', () => {
    const rulesProps = {
      categoryCounts: [],
      pins: [],
      disabledDays: [],
      isLoading: false,
      error: null,
      confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
      remove: vi.fn(),
      picker: baseProps(),
      categoryCountDraft: { category: '', count: '' },
      categoryCountOptions: [],
      setCategoryCountCategory: vi.fn(),
      setCategoryCountCount: vi.fn(),
      canSaveCategoryCount: false,
      saveCategoryCount: vi.fn(),
      pinDraft: { day: '', slot: '' },
      pinDayOptions: [],
      setPinDay: vi.fn(),
      setPinSlot: vi.fn(),
      pinRecipeId: null,
      selectPinRecipe: vi.fn(),
      canSavePin: false,
      savePin: vi.fn(),
      disabledDayDraft: { day: '' },
      disabledDayOptions: [],
      setDisabledDayDay: vi.fn(),
      canSaveDisabledDay: false,
      saveDisabledDay: vi.fn(),
    };
    render(<RulesView {...rulesProps} />);

    expect(screen.getByText(MESSAGES.LIBRARY_PICKER_NAME_LABEL)).not.toBeNull();
    expect(screen.getByText('Lentejas al curry')).not.toBeNull();
  });
});

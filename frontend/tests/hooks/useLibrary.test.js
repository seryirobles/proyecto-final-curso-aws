// @vitest-environment jsdom
// T30 (R9, R10, R11, R13, R14, R18): top-level library view state.
import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch, ApiError } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useLibrary } from '../../src/hooks/useLibrary.js';

function recipe(id, author, overrides = {}) {
  return {
    id,
    author,
    name: `Receta ${id}`,
    category: 'legume',
    servings: 4,
    estimatedTime: 30,
    ingredients: [],
    tools: [],
    procedure: [],
    ...overrides,
  };
}

// F4: a recipe with real content, to prove edit pre-fills/round-trips it
// instead of the empty arrays a blank form would send.
function fullRecipe(id, author) {
  return recipe(id, author, {
    servings: 2,
    ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
    tools: ['olla'],
    procedure: ['Sofreír la cebolla.'],
  });
}

function pollSnapshot(recipes) {
  return {
    data: { recipes },
    connectionLost: false,
    applyMutationMarker: vi.fn(),
    refetchNow: vi.fn(), // issue ui-not-reflecting-mutations
  };
}

// Non-empty sections (issue recipe-saved-without-required-sections, G-89):
// canSubmit now requires at least one ingredient/tool/procedure step.
function fillRequiredSections(result) {
  act(() => result.current.authoring.addIngredient());
  act(() => result.current.authoring.updateIngredient(0, 'name', 'lentejas'));
  act(() => result.current.authoring.updateIngredient(0, 'quantity', '300'));
  act(() => result.current.authoring.updateIngredient(0, 'unit', 'g'));
  act(() => result.current.authoring.addTool());
  act(() => result.current.authoring.updateTool(0, 'olla'));
  act(() => result.current.authoring.addProcedureStep());
  act(() => result.current.authoring.updateProcedureStep(0, 'Cocer las lentejas.'));
}

describe('useLibrary', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it('a name filter narrows the already-polled recipes client-side (R11)', () => {
    usePolling.mockReturnValue(
      pollSnapshot([recipe('r-1', 'Marta'), recipe('r-2', 'Diego', { name: 'Tortilla' })]),
    );
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.setName('r-1'));

    expect(result.current.recipes.map((r) => r.id)).toEqual(['r-1']);
  });

  it('a category filter narrows the already-polled recipes client-side (R13)', () => {
    usePolling.mockReturnValue(
      pollSnapshot([recipe('r-1', 'Marta'), recipe('r-2', 'Diego', { category: 'eggs' })]),
    );
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.setCategory('eggs'));

    expect(result.current.recipes.map((r) => r.id)).toEqual(['r-2']);
  });

  it('the poll always targets the unfiltered URI, never a filtered one (F1)', () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.setName('lentejas'));
    act(() => result.current.setCategory('legume'));

    for (const call of usePolling.mock.calls) {
      expect(call[0]).toBe('/v1/library/recipes');
    }
  });

  it('the filter state object has exactly the keys name/category, nothing else (R14)', () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    const { result } = renderHook(() => useLibrary());

    expect(Object.keys(result.current.filters).sort()).toEqual(['category', 'name']);
  });

  it('recipes from two different authors both render (R9)', () => {
    usePolling.mockReturnValue(pollSnapshot([recipe('r-1', 'Marta'), recipe('r-2', 'Diego')]));
    const { result } = renderHook(() => useLibrary());

    expect(result.current.recipes.map((r) => r.author)).toEqual(['Marta', 'Diego']);
  });

  it('remove routes through useConfirm before calling apiFetch (R18)', async () => {
    usePolling.mockReturnValue(pollSnapshot([recipe('r-1', 'Marta')]));
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.remove('r-1'));

    expect(result.current.confirm.pending).not.toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();

    await act(async () => result.current.confirm.confirm());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/library/recipes/r-1',
      expect.objectContaining({ method: 'DELETE' }),
    );
  });

  it('openAdd opens the authoring form for a new recipe (R10)', () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.openAdd());

    expect(result.current.isAuthoringOpen).toBe(true);
    expect(result.current.isEditing).toBe(false);
  });

  it('openEdit opens the authoring form for an existing recipe (R10)', () => {
    usePolling.mockReturnValue(pollSnapshot([recipe('r-1', 'Marta')]));
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.openEdit(recipe('r-1', 'Marta')));

    expect(result.current.isAuthoringOpen).toBe(true);
    expect(result.current.isEditing).toBe(true);
  });

  it('submitting the authoring form after openAdd posts to /v1/library/recipes (R10)', async () => {
    apiFetch.mockResolvedValue(null);
    usePolling.mockReturnValue(pollSnapshot([]));
    const { result } = renderHook(() => useLibrary());
    act(() => result.current.openAdd());
    act(() => result.current.authoring.updateField('name', 'Tortilla'));
    act(() => result.current.authoring.updateField('category', 'eggs'));
    fillRequiredSections(result);

    await act(async () => result.current.authoring.submit());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/library/recipes',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('openEdit pre-fills the authoring form from the recipe being edited (F4)', () => {
    usePolling.mockReturnValue(pollSnapshot([fullRecipe('r-1', 'Marta')]));
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.openEdit(fullRecipe('r-1', 'Marta')));

    expect(result.current.authoring.form).toEqual({
      name: 'Receta r-1',
      category: 'legume',
      servings: '2',
      estimatedTime: '30',
      ingredients: [{ name: 'lentejas', quantity: '300', unit: 'g' }],
      tools: ['olla'],
      procedure: ['Sofreír la cebolla.'],
    });
  });

  it('submitting an edit without changes round-trips the real ingredients/tools/procedure, not empty arrays (F4)', async () => {
    apiFetch.mockResolvedValue(null);
    usePolling.mockReturnValue(pollSnapshot([fullRecipe('r-1', 'Marta')]));
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.openEdit(fullRecipe('r-1', 'Marta')));
    await act(async () => result.current.authoring.submit());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/library/recipes/r-1',
      expect.objectContaining({
        method: 'PUT',
        body: {
          source: 'manual',
          recipe: {
            name: 'Receta r-1',
            category: 'legume',
            servings: 2,
            estimatedTime: 30,
            ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
            tools: ['olla'],
            procedure: ['Sofreír la cebolla.'],
          },
        },
      }),
    );
  });

  it('submitting the authoring form after openEdit puts to /v1/library/recipes/{id} (R10)', async () => {
    apiFetch.mockResolvedValue(null);
    usePolling.mockReturnValue(pollSnapshot([recipe('r-1', 'Marta')]));
    const { result } = renderHook(() => useLibrary());
    act(() => result.current.openEdit(recipe('r-1', 'Marta')));
    act(() => result.current.authoring.updateField('name', 'Tortilla'));
    act(() => result.current.authoring.updateField('category', 'eggs'));
    fillRequiredSections(result);

    await act(async () => result.current.authoring.submit());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/library/recipes/r-1',
      expect.objectContaining({ method: 'PUT' }),
    );
  });

  it('sets error to the mutation detail, es-ES verbatim, on a rejected submit (R15)', async () => {
    apiFetch.mockRejectedValue(
      new ApiError({ status: 409, code: 'DUPLICATE', detail: 'Ya existe.' }),
    );
    usePolling.mockReturnValue(pollSnapshot([]));
    const { result } = renderHook(() => useLibrary());
    act(() => result.current.openAdd());
    act(() => result.current.authoring.updateField('name', 'Tortilla'));
    act(() => result.current.authoring.updateField('category', 'eggs'));
    fillRequiredSections(result);

    await act(async () => result.current.authoring.submit());

    expect(result.current.error).toBe('Ya existe.');
  });

  it('active: false reaches its own picker AND the authoring pickers as enabled: false (App shell finding 1)', () => {
    usePolling.mockReturnValue(pollSnapshot([]));

    renderHook(() => useLibrary({ active: false }));

    // useLibrary's own picker is created first, before useRecipeAuthoring's two.
    const [ownPickerCall] = usePolling.mock.calls;
    expect(ownPickerCall[2]).toEqual({ enabled: false });
    usePolling.mock.calls.forEach((call) => expect(call[2].enabled).toBe(false));
  });

  it('openDetail resolves to a normalized recipe from an already-held row (R5)', () => {
    usePolling.mockReturnValue(pollSnapshot([recipe('r-1', 'Marta')]));
    const { result } = renderHook(() => useLibrary());

    act(() => result.current.openDetail(recipe('r-1', 'Marta')));

    expect(result.current.detail).toMatchObject({ name: 'Receta r-1', author: 'Marta' });
  });
});

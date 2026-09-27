// Shared authoring flow (T22, design.md section 5.1): three methods for
// candidate authoring, two for library authoring (R6-R8). "ai" drives
// useAiGeneration (feature 28). See progress/impl_frontend_spa.md, "The shared authoring flow".

import { useCallback, useMemo, useState } from 'react';
import { useLibraryPicker } from './useLibraryPicker.js';
import { useAiGeneration } from './useAiGeneration.js';

const CANDIDATE_METHODS = ['library', 'scratch', 'ai'];
const LIBRARY_METHODS = ['scratch', 'ai'];

function emptyForm() {
  return {
    name: '',
    category: '',
    servings: '',
    estimatedTime: '',
    ingredients: [],
    tools: [],
    procedure: [],
  };
}

function emptyIngredient() {
  return { name: '', quantity: '', unit: '' };
}

// Issue negative-ingredient-quantity (E4, E10): a non-blank value that is not
// strictly positive blocks submit. Blank is issue 5's territory (empty
// required field), not this rule's - see plan.md "Who owns which message".
function isInvalidPositive(value) {
  return value !== '' && !(Number(value) > 0);
}

// Inverse of buildManualRecipe, below - seeds the manual form from an
// existing recipe on edit (F4 fix round 1: openEdit used to open a blank
// form, so saving without re-typing everything wiped the real content).
function recipeToForm(recipe) {
  return {
    name: recipe.name ?? '',
    category: recipe.category ?? '',
    servings: recipe.servings != null ? String(recipe.servings) : '',
    estimatedTime: recipe.estimatedTime != null ? String(recipe.estimatedTime) : '',
    ingredients: (recipe.ingredients ?? []).map((ingredient) => ({
      name: ingredient.name ?? '',
      quantity: ingredient.quantity != null ? String(ingredient.quantity) : '',
      unit: ingredient.unit ?? '',
    })),
    tools: recipe.tools ?? [],
    procedure: recipe.procedure ?? [],
  };
}

// rest_api_contract.md section 3.1's `manual.recipe` shape. `quantity`,
// `servings` and `estimatedTime` are cast to their wire types - transport
// plumbing, not a computed value. `estimatedTime` is a minute count
// (FR-LIB-03, G-90 - supersedes G-85's free text for this field).
function buildManualRecipe(form) {
  return {
    name: form.name,
    category: form.category,
    servings: form.servings === '' ? null : Number(form.servings),
    estimatedTime: form.estimatedTime === '' ? null : Number(form.estimatedTime),
    ingredients: form.ingredients.map((ingredient) => ({
      name: ingredient.name,
      quantity: Number(ingredient.quantity),
      unit: ingredient.unit,
    })),
    tools: form.tools,
    procedure: form.procedure,
  };
}

// Free-text list fields (one item per line or comma) -> the wire's string lists.
function splitList(text) {
  return text
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter((item) => item !== '');
}

// rest_api_contract.md section 3.6: a picked reference recipe means a
// `reference` source; otherwise the ingredients and tools form a `specification`.
function buildAiSource(aiSpec, referenceRecipeId) {
  if (referenceRecipeId != null) {
    return {
      kind: 'reference',
      recipeId: referenceRecipeId,
      extraSpecifications: splitList(aiSpec.notes),
    };
  }
  return {
    kind: 'specification',
    ingredients: splitList(aiSpec.ingredients),
    tools: splitList(aiSpec.tools),
  };
}

// `aiTarget` is the slot being authored ({ weekId, day, slot }); library
// authoring has none (FR-CAND-03).
function buildAiTarget(mode, aiTarget) {
  if (mode === 'library') return { kind: 'library' };
  if (!aiTarget?.weekId) return null;
  return {
    kind: 'slot',
    weekId: aiTarget.weekId,
    day: Number(aiTarget.day),
    slot: Number(aiTarget.slot),
  };
}

export function useRecipeAuthoring({
  mode,
  onSubmit,
  initialRecipe = null,
  initialMethod = null,
  active = true,
  aiTarget = null,
}) {
  const methods = mode === 'candidate' ? CANDIDATE_METHODS : LIBRARY_METHODS;
  const [method, setMethod] = useState(initialMethod ?? methods[0]);
  const [form, setForm] = useState(() =>
    initialRecipe ? recipeToForm(initialRecipe) : emptyForm(),
  );
  // Re-seeds `form` when the edited recipe identity changes (F4). A
  // render-time comparison, not an effect - same technique as
  // useRecipeDetail's request-keyed isLoading, avoids set-state-in-effect.
  const [seededFrom, setSeededFrom] = useState(initialRecipe);
  if (initialRecipe !== seededFrom) {
    setSeededFrom(initialRecipe);
    setForm(initialRecipe ? recipeToForm(initialRecipe) : emptyForm());
  }
  const [libraryRecipeId, setLibraryRecipeId] = useState(null);
  const [referenceRecipeId, setReferenceRecipeId] = useState(null);
  const [aiSpec, setAiSpec] = useState({ ingredients: '', tools: '', notes: '' });
  // R12 - two of LibraryRecipePicker's three call sites live here (T27).
  // `enabled` ANDs with the incoming `active` per App shell Fix round 1,
  // finding 1 - see progress/impl_frontend_spa.md, "App shell".
  const libraryPicker = useLibraryPicker({ enabled: active && method === 'library' });
  const referencePicker = useLibraryPicker({ enabled: active && method === 'ai' });

  const updateField = useCallback((field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  }, []);

  const addIngredient = useCallback(() => {
    setForm((current) => ({
      ...current,
      ingredients: [...current.ingredients, emptyIngredient()],
    }));
  }, []);
  const updateIngredient = useCallback((index, field, value) => {
    setForm((current) => ({
      ...current,
      ingredients: current.ingredients.map((ingredient, i) =>
        i === index ? { ...ingredient, [field]: value } : ingredient,
      ),
    }));
  }, []);
  const removeIngredient = useCallback((index) => {
    setForm((current) => ({
      ...current,
      ingredients: current.ingredients.filter((_, i) => i !== index),
    }));
  }, []);

  const addTool = useCallback(() => {
    setForm((current) => ({ ...current, tools: [...current.tools, ''] }));
  }, []);
  const updateTool = useCallback((index, value) => {
    setForm((current) => ({
      ...current,
      tools: current.tools.map((tool, i) => (i === index ? value : tool)),
    }));
  }, []);
  const removeTool = useCallback((index) => {
    setForm((current) => ({ ...current, tools: current.tools.filter((_, i) => i !== index) }));
  }, []);

  const addProcedureStep = useCallback(() => {
    setForm((current) => ({ ...current, procedure: [...current.procedure, ''] }));
  }, []);
  const updateProcedureStep = useCallback((index, value) => {
    setForm((current) => ({
      ...current,
      procedure: current.procedure.map((step, i) => (i === index ? value : step)),
    }));
  }, []);
  const removeProcedureStep = useCallback((index) => {
    setForm((current) => ({
      ...current,
      procedure: current.procedure.filter((_, i) => i !== index),
    }));
  }, []);

  const updateAiSpec = useCallback((field, value) => {
    setAiSpec((current) => ({ ...current, [field]: value }));
  }, []);

  // R35: candidate authoring accepts through the `generation` source; the
  // library takes the previewed body as a manual recipe.
  const handleAccept = useCallback(
    ({ generationId, recipe }) => {
      if (mode === 'candidate') onSubmit({ source: 'generation', generationId });
      else onSubmit({ source: 'manual', recipe });
    },
    [mode, onSubmit],
  );
  const aiTargetBody = useMemo(
    () => buildAiTarget(mode, aiTarget),
    // Keyed by value so a fresh object with the same slot does not reset a run.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [mode, aiTarget?.weekId, aiTarget?.day, aiTarget?.slot],
  );
  const aiGeneration = useAiGeneration({ target: aiTargetBody, onAccept: handleAccept });
  const aiSource = useMemo(
    () => buildAiSource(aiSpec, referenceRecipeId),
    [aiSpec, referenceRecipeId],
  );
  const aiCanGenerate =
    aiTargetBody != null &&
    !aiGeneration.isLoading &&
    (aiSource.kind === 'reference' ||
      (aiSource.ingredients.length > 0 && aiSource.tools.length > 0));
  // R37: regenerate re-POSTs whatever the form holds now, adjusted or not.
  const generate = useCallback(() => aiGeneration.generate(aiSource), [aiGeneration, aiSource]);
  const ai = {
    phase: aiGeneration.phase,
    isLoading: aiGeneration.isLoading,
    recipe: aiGeneration.recipe,
    failureMessage: aiGeneration.failureMessage,
    canGenerate: aiCanGenerate,
    generate,
    regenerate: generate,
    accept: aiGeneration.accept,
    discard: aiGeneration.discard,
  };

  const canSubmit = useMemo(() => {
    if (method === 'scratch') {
      // Each section needs at least one item (issue
      // recipe-saved-without-required-sections, E6, G-89).
      const sectionsFilled =
        form.ingredients.length > 0 && form.tools.length > 0 && form.procedure.length > 0;
      if (!sectionsFilled) return false;
      if (form.ingredients.some((ingredient) => isInvalidPositive(ingredient.quantity))) {
        return false;
      }
      return !isInvalidPositive(form.servings);
    }
    if (method === 'library') return libraryRecipeId != null;
    return false; // ai submits through `ai.generate`, not `submit`
  }, [method, form, libraryRecipeId]);

  const submit = useCallback(() => {
    if (!canSubmit) return;
    if (method === 'scratch') {
      onSubmit({ source: 'manual', recipe: buildManualRecipe(form) });
    } else if (method === 'library') {
      onSubmit({ source: 'library', recipeId: libraryRecipeId });
    }
    // "ai" never reaches here - canSubmit is always false for it.
  }, [canSubmit, method, form, libraryRecipeId, onSubmit]);

  return {
    mode,
    methods,
    method,
    setMethod,
    form,
    updateField,
    addIngredient,
    updateIngredient,
    removeIngredient,
    addTool,
    updateTool,
    removeTool,
    addProcedureStep,
    updateProcedureStep,
    removeProcedureStep,
    libraryRecipeId,
    selectLibraryRecipe: setLibraryRecipeId,
    libraryPicker,
    referenceRecipeId,
    selectReferenceRecipe: setReferenceRecipeId,
    referencePicker,
    aiSpec,
    updateAiSpec,
    ai,
    canSubmit,
    submit,
  };
}

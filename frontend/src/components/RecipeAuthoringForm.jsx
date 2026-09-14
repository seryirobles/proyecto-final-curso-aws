// The shared authoring flow's form (T23, design.md section 5/5.1): method
// tabs plus manual-form fields, pure function of useRecipeAuthoring's return
// shape. See progress/impl_frontend_spa.md, "The shared authoring flow".

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_LABELS, UNIT_LABELS } from '../domain/labels.js';
import { LibraryRecipePicker } from './LibraryRecipePicker.jsx';

const METHOD_LABELS = {
  library: MESSAGES.RECIPE_AUTHORING_METHOD_LIBRARY,
  scratch: MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH,
  ai: MESSAGES.RECIPE_AUTHORING_METHOD_AI,
};

function tabStyle(isActive) {
  return {
    padding: tokens.space.sm,
    backgroundColor: isActive ? tokens.color.terraSoft : tokens.color.surface,
    border: `1px solid ${tokens.color.line}`,
  };
}

function ScratchFields({
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
  canSubmit,
  submit,
}) {
  return (
    <div>
      <label>
        {MESSAGES.RECIPE_AUTHORING_NAME_LABEL}
        <input
          type="text"
          value={form.name}
          onChange={(e) => updateField('name', e.target.value)}
        />
      </label>
      <label>
        {MESSAGES.RECIPE_AUTHORING_CATEGORY_LABEL}
        <select value={form.category} onChange={(e) => updateField('category', e.target.value)}>
          <option value="">{MESSAGES.RECIPE_AUTHORING_CATEGORY_PLACEHOLDER}</option>
          {Object.entries(CATEGORY_LABELS).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label>
        {MESSAGES.RECIPE_AUTHORING_SERVINGS_LABEL}
        <input
          type="text"
          value={form.servings}
          onChange={(e) => updateField('servings', e.target.value)}
        />
      </label>
      <label>
        {MESSAGES.RECIPE_AUTHORING_ESTIMATED_TIME_LABEL}
        <input
          type="text"
          value={form.estimatedTime}
          onChange={(e) => updateField('estimatedTime', e.target.value)}
        />
      </label>

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RECIPE_AUTHORING_INGREDIENTS_LABEL}</h3>
      {form.ingredients.map((ingredient, index) => (
        <div key={index} style={{ display: 'flex', gap: tokens.space.sm }}>
          <input
            type="text"
            placeholder={MESSAGES.RECIPE_AUTHORING_INGREDIENT_NAME_LABEL}
            value={ingredient.name}
            onChange={(e) => updateIngredient(index, 'name', e.target.value)}
          />
          <input
            type="number"
            placeholder={MESSAGES.RECIPE_AUTHORING_INGREDIENT_QUANTITY_LABEL}
            value={ingredient.quantity}
            onChange={(e) => updateIngredient(index, 'quantity', e.target.value)}
          />
          <select
            value={ingredient.unit}
            onChange={(e) => updateIngredient(index, 'unit', e.target.value)}
          >
            <option value="">{MESSAGES.RECIPE_AUTHORING_UNIT_PLACEHOLDER}</option>
            {Object.entries(UNIT_LABELS).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
          <button type="button" onClick={() => removeIngredient(index)}>
            {MESSAGES.RECIPE_AUTHORING_REMOVE_INGREDIENT}
          </button>
        </div>
      ))}
      <button type="button" onClick={addIngredient}>
        {MESSAGES.RECIPE_AUTHORING_ADD_INGREDIENT}
      </button>

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RECIPE_AUTHORING_TOOLS_LABEL}</h3>
      {form.tools.map((tool, index) => (
        <div key={index} style={{ display: 'flex', gap: tokens.space.sm }}>
          <input type="text" value={tool} onChange={(e) => updateTool(index, e.target.value)} />
          <button type="button" onClick={() => removeTool(index)}>
            {MESSAGES.RECIPE_AUTHORING_REMOVE_TOOL}
          </button>
        </div>
      ))}
      <button type="button" onClick={addTool}>
        {MESSAGES.RECIPE_AUTHORING_ADD_TOOL}
      </button>

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RECIPE_AUTHORING_PROCEDURE_LABEL}</h3>
      {form.procedure.map((step, index) => (
        <div key={index} style={{ display: 'flex', gap: tokens.space.sm }}>
          <input
            type="text"
            value={step}
            onChange={(e) => updateProcedureStep(index, e.target.value)}
          />
          <button type="button" onClick={() => removeProcedureStep(index)}>
            {MESSAGES.RECIPE_AUTHORING_REMOVE_STEP}
          </button>
        </div>
      ))}
      <button type="button" onClick={addProcedureStep}>
        {MESSAGES.RECIPE_AUTHORING_ADD_STEP}
      </button>

      <div style={{ marginTop: tokens.space.md }}>
        <button type="button" onClick={submit} disabled={!canSubmit}>
          {MESSAGES.RECIPE_AUTHORING_SUBMIT}
        </button>
      </div>
    </div>
  );
}

function AiStubFields({
  aiSpec,
  updateAiSpec,
  referenceRecipeId,
  selectReferenceRecipe,
  referencePicker,
}) {
  return (
    <div>
      <p style={{ color: tokens.color.ink2 }}>{MESSAGES.AI_GENERATION_UNAVAILABLE}</p>
      <label>
        {MESSAGES.RECIPE_AUTHORING_INGREDIENTS_LABEL}
        <textarea
          value={aiSpec.ingredients}
          onChange={(e) => updateAiSpec('ingredients', e.target.value)}
        />
      </label>
      <label>
        {MESSAGES.RECIPE_AUTHORING_TOOLS_LABEL}
        <textarea value={aiSpec.tools} onChange={(e) => updateAiSpec('tools', e.target.value)} />
      </label>
      <h3 style={{ margin: tokens.space.none }}>
        {MESSAGES.RECIPE_AUTHORING_REFERENCE_RECIPE_LABEL}
      </h3>
      <LibraryRecipePicker
        {...referencePicker}
        selectedRecipeId={referenceRecipeId}
        onSelect={selectReferenceRecipe}
      />
      <label>
        {MESSAGES.RECIPE_AUTHORING_NOTES_LABEL}
        <textarea value={aiSpec.notes} onChange={(e) => updateAiSpec('notes', e.target.value)} />
      </label>
      <div style={{ marginTop: tokens.space.md }}>
        <button type="button" disabled>
          {MESSAGES.RECIPE_AUTHORING_SUBMIT}
        </button>
      </div>
    </div>
  );
}

function LibraryMethodFields({
  libraryPicker,
  libraryRecipeId,
  selectLibraryRecipe,
  canSubmit,
  submit,
}) {
  return (
    <div>
      <LibraryRecipePicker
        {...libraryPicker}
        selectedRecipeId={libraryRecipeId}
        onSelect={selectLibraryRecipe}
      />
      <div style={{ marginTop: tokens.space.md }}>
        <button type="button" onClick={submit} disabled={!canSubmit}>
          {MESSAGES.RECIPE_AUTHORING_SUBMIT}
        </button>
      </div>
    </div>
  );
}

export function RecipeAuthoringForm(props) {
  const { methods, method, setMethod } = props;

  return (
    <div style={{ padding: tokens.space.lg, backgroundColor: tokens.color.surface }}>
      <div style={{ display: 'flex', gap: tokens.space.sm }}>
        {methods.map((m) => (
          <button key={m} type="button" onClick={() => setMethod(m)} style={tabStyle(m === method)}>
            {METHOD_LABELS[m]}
          </button>
        ))}
      </div>

      {method === 'library' ? <LibraryMethodFields {...props} /> : null}
      {method === 'scratch' ? <ScratchFields {...props} /> : null}
      {method === 'ai' ? <AiStubFields {...props} /> : null}
    </div>
  );
}

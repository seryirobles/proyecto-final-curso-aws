// The shared authoring flow's form (T23, design.md section 5/5.1): method
// tabs plus manual-form fields, pure function of useRecipeAuthoring's return
// shape. See progress/impl_frontend_spa.md, "The shared authoring flow".

// Non-AI parts styled off tokens; `AiStubFields` stays untouched - feature
// 28's territory (T87, design.md 10.6). See progress/impl_frontend_spa.md,
// "Tier E - library".

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_LABELS, UNIT_LABELS } from '../domain/labels.js';
import { LibraryRecipePicker } from './LibraryRecipePicker.jsx';

const METHOD_LABELS = {
  library: MESSAGES.RECIPE_AUTHORING_METHOD_LIBRARY,
  scratch: MESSAGES.RECIPE_AUTHORING_METHOD_SCRATCH,
  ai: MESSAGES.RECIPE_AUTHORING_METHOD_AI,
};

function tabStyle(isActive, method) {
  if (method === 'ai') {
    return {
      padding: `${tokens.space.xs} ${tokens.space.md}`,
      backgroundColor: isActive ? tokens.color.aub : tokens.color.aubSoft,
      color: isActive ? tokens.color.surface : tokens.color.aub,
      border: `1px solid ${tokens.color.aub}`,
      borderRadius: tokens.radius.pill,
      fontWeight: 700,
      fontSize: tokens.fontSize.sm,
    };
  }
  return {
    padding: `${tokens.space.xs} ${tokens.space.md}`,
    backgroundColor: isActive ? tokens.color.terraSoft : tokens.color.surface,
    color: isActive ? tokens.color.terraDeep : tokens.color.ink2,
    border: `1px solid ${tokens.color.line}`,
    borderRadius: tokens.radius.pill,
    fontWeight: 700,
    fontSize: tokens.fontSize.sm,
  };
}

const fieldLabelStyle = {
  display: 'flex',
  flexDirection: 'column',
  gap: tokens.space.xs,
  fontFamily: tokens.fontFamily.label,
  fontSize: tokens.fontSize.xs,
  color: tokens.color.ink2,
  marginBottom: tokens.space.sm,
};

const fieldInputStyle = {
  border: `1px solid ${tokens.color.line2}`,
  backgroundColor: tokens.color.surface2,
  borderRadius: tokens.radius.sm,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  color: tokens.color.ink,
  fontSize: tokens.fontSize.sm,
};

const sectionHeaderStyle = {
  margin: `${tokens.space.md} 0 ${tokens.space.sm}`,
  fontFamily: tokens.fontFamily.heading,
  fontSize: tokens.fontSize.sm,
  color: tokens.color.ink,
};

const rowButtonStyle = {
  border: `1px solid ${tokens.color.line2}`,
  backgroundColor: tokens.color.surface2,
  color: tokens.color.ink2,
  borderRadius: tokens.radius.sm,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  fontSize: tokens.fontSize.xs,
};

const addRowButtonStyle = {
  border: `1px dashed ${tokens.color.line2}`,
  backgroundColor: 'transparent',
  color: tokens.color.terra,
  borderRadius: tokens.radius.sm,
  padding: tokens.space.xs,
  fontSize: tokens.fontSize.xs,
  width: '100%',
};

const submitButtonStyle = {
  border: 'none',
  backgroundColor: tokens.color.terra,
  color: tokens.color.surface,
  borderRadius: tokens.radius.sm,
  padding: `${tokens.space.sm} ${tokens.space.md}`,
  fontWeight: 700,
  fontSize: tokens.fontSize.sm,
};

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
      <label style={fieldLabelStyle}>
        {MESSAGES.RECIPE_AUTHORING_NAME_LABEL}
        <input
          type="text"
          value={form.name}
          onChange={(e) => updateField('name', e.target.value)}
          style={fieldInputStyle}
        />
      </label>
      <label style={fieldLabelStyle}>
        {MESSAGES.RECIPE_AUTHORING_CATEGORY_LABEL}
        <select
          value={form.category}
          onChange={(e) => updateField('category', e.target.value)}
          style={fieldInputStyle}
        >
          <option value="">{MESSAGES.RECIPE_AUTHORING_CATEGORY_PLACEHOLDER}</option>
          {Object.entries(CATEGORY_LABELS).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label style={fieldLabelStyle}>
        {MESSAGES.RECIPE_AUTHORING_SERVINGS_LABEL}
        <input
          type="number"
          step="1"
          min="0"
          value={form.servings}
          onChange={(e) => updateField('servings', e.target.value)}
          style={fieldInputStyle}
        />
        {/* Issue negative-ingredient-quantity, E11 - non-blank, <= 0 (G-91).
            honey - same warning idiom as ConnectionLostBanner/SetPasswordView. */}
        {form.servings !== '' && Number(form.servings) <= 0 ? (
          <span style={{ color: tokens.color.honey, fontSize: tokens.fontSize.xs }}>
            {MESSAGES.RECIPE_AUTHORING_INVALID_SERVINGS}
          </span>
        ) : null}
      </label>
      <label style={fieldLabelStyle}>
        {MESSAGES.RECIPE_AUTHORING_ESTIMATED_TIME_LABEL}
        <input
          type="number"
          step="1"
          min="0"
          max="6000"
          value={form.estimatedTime}
          onChange={(e) => updateField('estimatedTime', e.target.value)}
          style={fieldInputStyle}
        />
      </label>

      <h3 style={sectionHeaderStyle}>{MESSAGES.RECIPE_AUTHORING_INGREDIENTS_LABEL}</h3>
      {form.ingredients.map((ingredient, index) => (
        <div
          key={index}
          style={{ display: 'flex', gap: tokens.space.sm, marginBottom: tokens.space.xs }}
        >
          <input
            type="text"
            placeholder={MESSAGES.RECIPE_AUTHORING_INGREDIENT_NAME_LABEL}
            value={ingredient.name}
            onChange={(e) => updateIngredient(index, 'name', e.target.value)}
            style={fieldInputStyle}
          />
          <input
            type="number"
            placeholder={MESSAGES.RECIPE_AUTHORING_INGREDIENT_QUANTITY_LABEL}
            value={ingredient.quantity}
            min="0"
            onChange={(e) => updateIngredient(index, 'quantity', e.target.value)}
            style={{ ...fieldInputStyle, width: '80px' }}
          />
          {/* Issue negative-ingredient-quantity, E5 - non-blank, <= 0 (Part H). */}
          {ingredient.quantity !== '' && Number(ingredient.quantity) <= 0 ? (
            <span style={{ color: tokens.color.honey, fontSize: tokens.fontSize.xs }}>
              {MESSAGES.RECIPE_AUTHORING_INVALID_QUANTITY}
            </span>
          ) : null}
          <select
            value={ingredient.unit}
            onChange={(e) => updateIngredient(index, 'unit', e.target.value)}
            style={fieldInputStyle}
          >
            <option value="">{MESSAGES.RECIPE_AUTHORING_UNIT_PLACEHOLDER}</option>
            {Object.entries(UNIT_LABELS).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
          <button type="button" onClick={() => removeIngredient(index)} style={rowButtonStyle}>
            {MESSAGES.RECIPE_AUTHORING_REMOVE_INGREDIENT}
          </button>
        </div>
      ))}
      {/* Issue recipe-saved-without-required-sections, E8 - same honey idiom
          as the servings/quantity warnings above. */}
      {form.ingredients.length === 0 ? (
        <span style={{ color: tokens.color.honey, fontSize: tokens.fontSize.xs }}>
          {MESSAGES.RECIPE_AUTHORING_MISSING_INGREDIENTS}
        </span>
      ) : null}
      <button type="button" onClick={addIngredient} style={addRowButtonStyle}>
        {MESSAGES.RECIPE_AUTHORING_ADD_INGREDIENT}
      </button>

      <h3 style={sectionHeaderStyle}>{MESSAGES.RECIPE_AUTHORING_TOOLS_LABEL}</h3>
      {form.tools.map((tool, index) => (
        <div
          key={index}
          style={{ display: 'flex', gap: tokens.space.sm, marginBottom: tokens.space.xs }}
        >
          <input
            type="text"
            value={tool}
            onChange={(e) => updateTool(index, e.target.value)}
            style={fieldInputStyle}
          />
          <button type="button" onClick={() => removeTool(index)} style={rowButtonStyle}>
            {MESSAGES.RECIPE_AUTHORING_REMOVE_TOOL}
          </button>
        </div>
      ))}
      {form.tools.length === 0 ? (
        <span style={{ color: tokens.color.honey, fontSize: tokens.fontSize.xs }}>
          {MESSAGES.RECIPE_AUTHORING_MISSING_TOOLS}
        </span>
      ) : null}
      <button type="button" onClick={addTool} style={addRowButtonStyle}>
        {MESSAGES.RECIPE_AUTHORING_ADD_TOOL}
      </button>

      <h3 style={sectionHeaderStyle}>{MESSAGES.RECIPE_AUTHORING_PROCEDURE_LABEL}</h3>
      {form.procedure.map((step, index) => (
        <div
          key={index}
          style={{ display: 'flex', gap: tokens.space.sm, marginBottom: tokens.space.xs }}
        >
          <input
            type="text"
            value={step}
            onChange={(e) => updateProcedureStep(index, e.target.value)}
            style={fieldInputStyle}
          />
          <button type="button" onClick={() => removeProcedureStep(index)} style={rowButtonStyle}>
            {MESSAGES.RECIPE_AUTHORING_REMOVE_STEP}
          </button>
        </div>
      ))}
      {form.procedure.length === 0 ? (
        <span style={{ color: tokens.color.honey, fontSize: tokens.fontSize.xs }}>
          {MESSAGES.RECIPE_AUTHORING_MISSING_PROCEDURE}
        </span>
      ) : null}
      <button type="button" onClick={addProcedureStep} style={addRowButtonStyle}>
        {MESSAGES.RECIPE_AUTHORING_ADD_STEP}
      </button>

      <div style={{ marginTop: tokens.space.md }}>
        <button type="button" onClick={submit} disabled={!canSubmit} style={submitButtonStyle}>
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
        <button type="button" onClick={submit} disabled={!canSubmit} style={submitButtonStyle}>
          {MESSAGES.RECIPE_AUTHORING_SUBMIT}
        </button>
      </div>
    </div>
  );
}

export function RecipeAuthoringForm(props) {
  const { methods, method, setMethod } = props;

  return (
    <div
      style={{
        padding: tokens.space.lg,
        backgroundColor: tokens.color.surface,
        border: `1px solid ${tokens.color.line}`,
        borderRadius: tokens.radius.md,
        boxShadow: tokens.shadow.sm,
      }}
    >
      <div style={{ display: 'flex', gap: tokens.space.sm, marginBottom: tokens.space.md }}>
        {methods.map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMethod(m)}
            style={tabStyle(m === method, m)}
          >
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

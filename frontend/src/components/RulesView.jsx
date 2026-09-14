// The rules screen (T33; design.md section 5). Dropdown-only add/edit per
// type; PUT is upsert-by-natural-key. See progress/impl_frontend_spa.md,
// "Rules view (T32-T34)" for the design gaps this fills.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_LABELS, DAY_LABELS, SLOT_LABELS } from '../domain/labels.js';
import { RULE_COUNT_OPTIONS, describeRule } from '../hooks/useRules.js';
import { EmptyState } from './EmptyState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { LibraryRecipePicker } from './LibraryRecipePicker.jsx';

function RuleRow({ label, onRemove }) {
  return (
    <li>
      <span>{label}</span>
      <button type="button" onClick={onRemove}>
        {MESSAGES.RULES_REMOVE}
      </button>
    </li>
  );
}

export function RulesView({
  categoryCounts,
  pins,
  disabledDays,
  isLoading,
  error,
  confirm,
  remove,
  picker,
  categoryCountDraft,
  setCategoryCountCategory,
  setCategoryCountCount,
  canSaveCategoryCount,
  saveCategoryCount,
  pinDraft,
  setPinDay,
  setPinSlot,
  pinRecipeId,
  selectPinRecipe,
  canSavePin,
  savePin,
  disabledDayDraft,
  setDisabledDayDay,
  canSaveDisabledDay,
  saveDisabledDay,
}) {
  if (isLoading) return <LoadingState />;

  const isEmpty = categoryCounts.length === 0 && pins.length === 0 && disabledDays.length === 0;

  return (
    <div>
      <h2 style={{ margin: tokens.space.none }}>{MESSAGES.RULES_VIEW_TITLE}</h2>
      {error ? <p style={{ color: tokens.color.ink, padding: tokens.space.md }}>{error}</p> : null}

      {isEmpty ? <EmptyState message={MESSAGES.RULES_VIEW_EMPTY} /> : null}

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RULES_CATEGORY_COUNT_SECTION_TITLE}</h3>
      {categoryCounts.length > 0 ? (
        <ul>
          {categoryCounts.map((rule) => (
            <RuleRow key={rule.category} label={describeRule(rule)} onRemove={() => remove(rule)} />
          ))}
        </ul>
      ) : null}
      <div style={{ display: 'flex', gap: tokens.space.sm }}>
        <label>
          {MESSAGES.RULES_CATEGORY_LABEL}
          <select
            value={categoryCountDraft.category}
            onChange={(e) => setCategoryCountCategory(e.target.value)}
          >
            <option value="">{MESSAGES.RULES_CATEGORY_PLACEHOLDER}</option>
            {Object.entries(CATEGORY_LABELS).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          {MESSAGES.RULES_COUNT_LABEL}
          <select
            value={categoryCountDraft.count}
            onChange={(e) => setCategoryCountCount(e.target.value)}
          >
            <option value="">{MESSAGES.RULES_COUNT_PLACEHOLDER}</option>
            {RULE_COUNT_OPTIONS.map((count) => (
              <option key={count} value={count}>
                {count}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={saveCategoryCount} disabled={!canSaveCategoryCount}>
          {MESSAGES.RULES_SAVE}
        </button>
      </div>

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RULES_PIN_SECTION_TITLE}</h3>
      {pins.length > 0 ? (
        <ul>
          {pins.map((rule) => (
            <RuleRow
              key={`${rule.day}#${rule.slot}`}
              label={`${describeRule(rule)} · ${rule.recipeName}`}
              onRemove={() => remove(rule)}
            />
          ))}
        </ul>
      ) : null}
      <div style={{ display: 'flex', gap: tokens.space.sm }}>
        <label>
          {MESSAGES.RULES_DAY_LABEL}
          <select value={pinDraft.day} onChange={(e) => setPinDay(e.target.value)}>
            <option value="">{MESSAGES.RULES_DAY_PLACEHOLDER}</option>
            {Object.entries(DAY_LABELS).map(([day, label]) => (
              <option key={day} value={day}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          {MESSAGES.RULES_SLOT_LABEL}
          <select value={pinDraft.slot} onChange={(e) => setPinSlot(e.target.value)}>
            <option value="">{MESSAGES.RULES_SLOT_PLACEHOLDER}</option>
            {Object.entries(SLOT_LABELS).map(([slot, label]) => (
              <option key={slot} value={slot}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <LibraryRecipePicker {...picker} selectedRecipeId={pinRecipeId} onSelect={selectPinRecipe} />
      <button type="button" onClick={savePin} disabled={!canSavePin}>
        {MESSAGES.RULES_SAVE}
      </button>

      <h3 style={{ margin: tokens.space.none }}>{MESSAGES.RULES_DISABLED_DAY_SECTION_TITLE}</h3>
      {disabledDays.length > 0 ? (
        <ul>
          {disabledDays.map((rule) => (
            <RuleRow key={rule.day} label={describeRule(rule)} onRemove={() => remove(rule)} />
          ))}
        </ul>
      ) : null}
      <div style={{ display: 'flex', gap: tokens.space.sm }}>
        <label>
          {MESSAGES.RULES_DAY_LABEL}
          <select value={disabledDayDraft.day} onChange={(e) => setDisabledDayDay(e.target.value)}>
            <option value="">{MESSAGES.RULES_DAY_PLACEHOLDER}</option>
            {Object.entries(DAY_LABELS).map(([day, label]) => (
              <option key={day} value={day}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={saveDisabledDay} disabled={!canSaveDisabledDay}>
          {MESSAGES.RULES_SAVE}
        </button>
      </div>

      <ConfirmDialog
        pending={confirm.pending}
        onConfirm={confirm.confirm}
        onCancel={confirm.cancel}
      />
    </div>
  );
}

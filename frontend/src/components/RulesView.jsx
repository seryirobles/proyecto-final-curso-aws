// The rules screen (T33; design.md section 5). Dropdown-only add/edit per
// type; PUT is upsert-by-natural-key. See progress/impl_frontend_spa.md,
// "Rules view (T32-T34)" for the design gaps this fills.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_LABELS, SLOT_LABELS } from '../domain/labels.js';
import { describeRule } from '../hooks/useRules.js';
import {
  selectStyle,
  primaryButtonStyle,
  ghostButtonStyle,
  listResetStyle,
  listRowStyle,
  accentDotStyle,
  cardStyle,
  headingStyle,
} from '../tokens/controlStyles.js';
import { EmptyState } from './EmptyState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { LibraryRecipePicker } from './LibraryRecipePicker.jsx';

function RuleRow({ label, onRemove }) {
  return (
    <li style={listRowStyle}>
      <span>{label}</span>
      <button type="button" onClick={onRemove} style={ghostButtonStyle}>
        {MESSAGES.RULES_REMOVE}
      </button>
    </li>
  );
}

const ruleGroupStyle = { ...cardStyle, marginTop: tokens.space.md };

// Group heading row: accent dot (prototype line 310/323/347) + title. One
// fixed colour per group, mirroring the "Días sin generación" -> aub match.
const ruleGroupHeadingRowStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: tokens.space.xs,
};

function RuleGroupHeading({ accentColor, children }) {
  return (
    <div style={ruleGroupHeadingRowStyle}>
      <span style={accentDotStyle(accentColor)} />
      <h3 style={headingStyle}>{children}</h3>
    </div>
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
  categoryCountOptions,
  setCategoryCountCategory,
  setCategoryCountCount,
  canSaveCategoryCount,
  saveCategoryCount,
  pinDraft,
  pinDayOptions,
  setPinDay,
  setPinSlot,
  pinRecipeId,
  selectPinRecipe,
  canSavePin,
  savePin,
  disabledDayDraft,
  disabledDayOptions,
  setDisabledDayDay,
  canSaveDisabledDay,
  saveDisabledDay,
}) {
  if (isLoading) return <LoadingState />;

  const isEmpty = categoryCounts.length === 0 && pins.length === 0 && disabledDays.length === 0;

  return (
    <div>
      <h2
        style={{
          margin: tokens.space.none,
          fontFamily: tokens.fontFamily.heading,
          fontSize: tokens.fontSize.xl,
        }}
      >
        {MESSAGES.RULES_VIEW_TITLE}
      </h2>
      {error ? <p style={{ color: tokens.color.ink, padding: tokens.space.md }}>{error}</p> : null}

      {isEmpty ? <EmptyState message={MESSAGES.RULES_VIEW_EMPTY} /> : null}

      <div style={ruleGroupStyle}>
        <RuleGroupHeading accentColor={tokens.color.olive}>
          {MESSAGES.RULES_CATEGORY_COUNT_SECTION_TITLE}
        </RuleGroupHeading>
        {categoryCounts.length > 0 ? (
          <ul style={listResetStyle}>
            {categoryCounts.map((rule) => (
              <RuleRow
                key={rule.category}
                label={describeRule(rule)}
                onRemove={() => remove(rule)}
              />
            ))}
          </ul>
        ) : null}
        <div style={{ display: 'flex', gap: tokens.space.sm, marginTop: tokens.space.sm }}>
          <label>
            {MESSAGES.RULES_CATEGORY_LABEL}
            <select
              value={categoryCountDraft.category}
              onChange={(e) => setCategoryCountCategory(e.target.value)}
              style={selectStyle}
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
              style={selectStyle}
            >
              <option value="">{MESSAGES.RULES_COUNT_PLACEHOLDER}</option>
              {categoryCountOptions.map((count) => (
                <option key={count} value={count}>
                  {count}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={saveCategoryCount}
            disabled={!canSaveCategoryCount}
            style={primaryButtonStyle(!canSaveCategoryCount)}
          >
            {MESSAGES.RULES_SAVE}
          </button>
        </div>
      </div>

      <div style={ruleGroupStyle}>
        <RuleGroupHeading accentColor={tokens.color.honey}>
          {MESSAGES.RULES_PIN_SECTION_TITLE}
        </RuleGroupHeading>
        {pins.length > 0 ? (
          <ul style={listResetStyle}>
            {pins.map((rule) => (
              <RuleRow
                key={`${rule.day}#${rule.slot}`}
                label={`${describeRule(rule)} · ${rule.recipeName}`}
                onRemove={() => remove(rule)}
              />
            ))}
          </ul>
        ) : null}
        <div style={{ display: 'flex', gap: tokens.space.sm, marginTop: tokens.space.sm }}>
          <label>
            {MESSAGES.RULES_DAY_LABEL}
            <select
              value={pinDraft.day}
              onChange={(e) => setPinDay(e.target.value)}
              style={selectStyle}
            >
              <option value="">{MESSAGES.RULES_DAY_PLACEHOLDER}</option>
              {pinDayOptions.map(([day, label]) => (
                <option key={day} value={day}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            {MESSAGES.RULES_SLOT_LABEL}
            <select
              value={pinDraft.slot}
              onChange={(e) => setPinSlot(e.target.value)}
              style={selectStyle}
            >
              <option value="">{MESSAGES.RULES_SLOT_PLACEHOLDER}</option>
              {Object.entries(SLOT_LABELS).map(([slot, label]) => (
                <option key={slot} value={slot}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <LibraryRecipePicker
          {...picker}
          selectedRecipeId={pinRecipeId}
          onSelect={selectPinRecipe}
        />
        <button
          type="button"
          onClick={savePin}
          disabled={!canSavePin}
          style={primaryButtonStyle(!canSavePin)}
        >
          {MESSAGES.RULES_SAVE}
        </button>
      </div>

      <div style={ruleGroupStyle}>
        <RuleGroupHeading accentColor={tokens.color.aub}>
          {MESSAGES.RULES_DISABLED_DAY_SECTION_TITLE}
        </RuleGroupHeading>
        {disabledDays.length > 0 ? (
          <ul style={listResetStyle}>
            {disabledDays.map((rule) => (
              <RuleRow key={rule.day} label={describeRule(rule)} onRemove={() => remove(rule)} />
            ))}
          </ul>
        ) : null}
        <div style={{ display: 'flex', gap: tokens.space.sm, marginTop: tokens.space.sm }}>
          <label>
            {MESSAGES.RULES_DAY_LABEL}
            <select
              value={disabledDayDraft.day}
              onChange={(e) => setDisabledDayDay(e.target.value)}
              style={selectStyle}
            >
              <option value="">{MESSAGES.RULES_DAY_PLACEHOLDER}</option>
              {disabledDayOptions.map(([day, label]) => (
                <option key={day} value={day}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={saveDisabledDay}
            disabled={!canSaveDisabledDay}
            style={primaryButtonStyle(!canSaveDisabledDay)}
          >
            {MESSAGES.RULES_SAVE}
          </button>
        </div>
      </div>

      <ConfirmDialog
        pending={confirm.pending}
        onConfirm={confirm.confirm}
        onCancel={confirm.cancel}
      />
    </div>
  );
}

// Dropdown-only editors for the rules of one generation run (FR-RULE-05).
// They write the hook's local draft and never call a /v1/rules endpoint;
// the options come from `availableOptions` (FR-RULE-07).

import { useState } from 'react';
import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_LABELS, DAY_LABELS } from '../domain/labels.js';
import {
  selectStyle,
  secondaryButtonStyle,
  listResetStyle,
  listRowStyle,
  headingStyle,
  targetStyle,
} from '../tokens/controlStyles.js';
import { VIEWPORT } from '../hooks/useViewport.js';

const groupStyle = { marginTop: tokens.space.sm };
const formStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: tokens.space.sm,
  alignItems: 'flex-end',
  marginTop: tokens.space.sm,
};

export function RuleOverrideEditor({
  draft,
  availableOptions,
  setCategoryCount,
  setDisabledDays,
  viewport = VIEWPORT.WIDE,
}) {
  const [category, setCategory] = useState('');
  const [count, setCount] = useState('');
  const [day, setDay] = useState('');
  const target = targetStyle(viewport);
  const control = { ...selectStyle, ...target };
  const button = { ...secondaryButtonStyle, ...target };

  const max = availableOptions?.maxCountByCategory?.[category] ?? 0;
  const countOptions = category === '' ? [] : Array.from({ length: max }, (_, i) => i + 1);
  const dayOptions = (availableOptions?.daysAvailableToDisable ?? []).filter(
    (candidate) => !draft.disabledDays.includes(candidate),
  );

  const addCategoryCount = (e) => {
    e.preventDefault();
    if (category === '' || count === '') return;
    setCategoryCount(category, Number(count));
    setCategory('');
    setCount('');
  };
  const addDisabledDay = (e) => {
    e.preventDefault();
    if (day === '') return;
    setDisabledDays([...draft.disabledDays, Number(day)].sort((a, b) => a - b));
    setDay('');
  };

  return (
    <div>
      <div style={groupStyle}>
        <h4 style={headingStyle}>{MESSAGES.RULES_CATEGORY_COUNT_SECTION_TITLE}</h4>
        <ul style={listResetStyle}>
          {draft.categoryCounts.map((entry) => (
            <li key={entry.category} style={listRowStyle}>
              <span>{`${CATEGORY_LABELS[entry.category] ?? entry.category} × ${entry.count}`}</span>
              <button
                type="button"
                onClick={() => setCategoryCount(entry.category, null)}
                style={button}
              >
                {MESSAGES.WEEK_GEN_OVERRIDE_REMOVE}
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={addCategoryCount} style={formStyle}>
          <label>
            {MESSAGES.RULES_CATEGORY_LABEL}
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setCount('');
              }}
              style={control}
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
            <select value={count} onChange={(e) => setCount(e.target.value)} style={control}>
              <option value="">{MESSAGES.RULES_COUNT_PLACEHOLDER}</option>
              {countOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={category === '' || count === ''} style={button}>
            {MESSAGES.WEEK_GEN_OVERRIDE_ADD}
          </button>
        </form>
      </div>

      <div style={groupStyle}>
        <h4 style={headingStyle}>{MESSAGES.RULES_DISABLED_DAY_SECTION_TITLE}</h4>
        <ul style={listResetStyle}>
          {draft.disabledDays.map((entry) => (
            <li key={entry} style={listRowStyle}>
              <span>{DAY_LABELS[entry]}</span>
              <button
                type="button"
                onClick={() => setDisabledDays(draft.disabledDays.filter((d) => d !== entry))}
                style={button}
              >
                {MESSAGES.WEEK_GEN_OVERRIDE_REMOVE}
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={addDisabledDay} style={formStyle}>
          <label>
            {MESSAGES.RULES_DAY_LABEL}
            <select value={day} onChange={(e) => setDay(e.target.value)} style={control}>
              <option value="">{MESSAGES.RULES_DAY_PLACEHOLDER}</option>
              {dayOptions.map((option) => (
                <option key={option} value={option}>
                  {DAY_LABELS[option]}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={day === ''} style={button}>
            {MESSAGES.WEEK_GEN_OVERRIDE_ADD}
          </button>
        </form>
      </div>
    </div>
  );
}

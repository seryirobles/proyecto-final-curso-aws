// The whole-week generation panel (feature 35, design.md section 3-4): an
// in-flow section with a configuring state and a running/finished report.
// Pure function of `useWeekGeneration`'s return shape.

import { useRef } from 'react';
import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { formatNumber } from '../locale.js';
import { DAY_LABELS, SLOT_LABELS, MODE_LABELS, MODE_HELP } from '../domain/labels.js';
import { describeRule } from '../hooks/useRules.js';
import { retryKey } from '../hooks/useWeekGeneration.js';
import { useScrollIntoView } from '../hooks/useScrollIntoView.js';
import { VIEWPORT } from '../hooks/useViewport.js';
import {
  cardStyle,
  headingStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  listResetStyle,
  listRowStyle,
  targetStyle,
  weekGridColumns,
} from '../tokens/controlStyles.js';
import { Banner } from './Banner.jsx';
import { LoadingState } from './LoadingState.jsx';
import { WeekLabel } from './WeekLabel.jsx';
import { RuleOverrideEditor } from './RuleOverrideEditor.jsx';

const NO_PENDING = new Set();
// Any tone but 'error' renders the Banner as role="status".
const NOT_ERROR_TONE = 'status';
const MODES = ['library_only', 'ai_only', 'mix'];

const panelStyle = {
  ...cardStyle,
  marginTop: tokens.space.md,
  scrollMarginTop: `calc(${tokens.layout.headerHeight} + ${tokens.layout.dayStripHeight})`,
};
const noteStyle = { color: tokens.color.ink2, margin: `${tokens.space.sm} ${tokens.space.none}` };

function slotRowLabel(row, retry, isRetrying, target) {
  if (row.state === 'pinned') return <span>{MESSAGES.WEEK_GEN_SLOT_PINNED}</span>;
  if (row.state === 'done') return <span>{MESSAGES.WEEK_GEN_SLOT_DONE}</span>;
  if (row.state === 'running') return <span>{MESSAGES.WEEK_GEN_SLOT_RUNNING}</span>;
  return (
    <>
      <span>{row.message || MESSAGES.GENERIC_ERROR}</span>
      <button
        type="button"
        onClick={() => retry(row.day, row.slot)}
        disabled={isRetrying}
        style={{ ...secondaryButtonStyle, ...target }}
      >
        {MESSAGES.WEEK_GEN_RETRY}
      </button>
    </>
  );
}

function Configuring({
  designation,
  mode,
  setMode,
  rules,
  rulesLoading,
  availableOptions,
  overrideDraft,
  startOverride,
  setCategoryCount,
  setDisabledDays,
  submit,
  close,
  isSubmitting,
  error,
  viewport,
}) {
  const target = targetStyle(viewport);
  return (
    <>
      {designation === 'current' ? <p style={noteStyle}>{MESSAGES.WEEK_GEN_CURRENT_NOTE}</p> : null}
      <p style={noteStyle}>{MESSAGES.WEEK_GEN_KEPT_NOTE}</p>
      <fieldset>
        <legend>{MESSAGES.WEEK_GEN_MODE_LEGEND}</legend>
        {MODES.map((code) => (
          <label
            key={code}
            style={{
              ...target,
              display: 'flex',
              alignItems: 'center',
              gap: tokens.space.sm,
            }}
          >
            <input
              type="radio"
              name="week-generation-mode"
              value={code}
              checked={mode === code}
              onChange={() => setMode(code)}
            />
            <span>
              {MODE_LABELS[code]}
              <br />
              <span style={{ color: tokens.color.ink2 }}>{MODE_HELP[code]}</span>
            </span>
          </label>
        ))}
      </fieldset>
      <h4 style={{ ...headingStyle, marginTop: tokens.space.md }}>
        {MESSAGES.WEEK_GEN_RULES_TITLE}
      </h4>
      {rulesLoading ? (
        <LoadingState message={MESSAGES.WEEK_GEN_RULES_LOADING} />
      ) : (
        <>
          {rules.length === 0 ? (
            <p style={noteStyle}>{MESSAGES.WEEK_GEN_RULES_EMPTY}</p>
          ) : (
            <ul style={listResetStyle}>
              {rules.map((rule) => (
                <li
                  key={`${rule.type}-${rule.category ?? ''}-${rule.day ?? ''}-${rule.slot ?? ''}`}
                  style={listRowStyle}
                >
                  {rule.type === 'pin'
                    ? `${describeRule(rule)} · ${rule.recipeName}`
                    : describeRule(rule)}
                </li>
              ))}
            </ul>
          )}
          {overrideDraft ? (
            <>
              <p style={noteStyle}>{MESSAGES.WEEK_GEN_OVERRIDE_NOTE}</p>
              <RuleOverrideEditor
                draft={overrideDraft}
                availableOptions={availableOptions}
                setCategoryCount={setCategoryCount}
                setDisabledDays={setDisabledDays}
                viewport={viewport}
              />
            </>
          ) : (
            <button
              type="button"
              onClick={startOverride}
              style={{ ...secondaryButtonStyle, ...target }}
            >
              {MESSAGES.WEEK_GEN_OVERRIDE_TOGGLE}
            </button>
          )}
        </>
      )}
      <Banner>{error}</Banner>
      <div style={{ display: 'flex', gap: tokens.space.sm, marginTop: tokens.space.md }}>
        <button
          type="button"
          onClick={submit}
          disabled={isSubmitting}
          style={{ ...primaryButtonStyle(isSubmitting), ...target }}
        >
          {isSubmitting ? MESSAGES.WEEK_GEN_SUBMITTING : MESSAGES.WEEK_GEN_CONFIRM}
        </button>
        <button type="button" onClick={close} style={{ ...secondaryButtonStyle, ...target }}>
          {MESSAGES.WEEK_GEN_CANCEL}
        </button>
      </div>
    </>
  );
}

function Report({
  phase,
  slots,
  progress,
  skippedPins,
  retrySlot,
  pending,
  error,
  dismiss,
  viewport,
}) {
  const target = targetStyle(viewport);
  const days = [...new Set(slots.map((row) => row.day))];
  return (
    <>
      {phase === 'running' ? (
        <p role="status">
          {MESSAGES.WEEK_GEN_PROGRESS(formatNumber(progress.done), formatNumber(progress.total))}
        </p>
      ) : null}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: weekGridColumns(viewport),
          gap: tokens.space.md,
        }}
      >
        {days.map((day) => (
          <div key={day} style={cardStyle}>
            <h4 style={headingStyle}>{DAY_LABELS[day]}</h4>
            <ul style={listResetStyle}>
              {slots
                .filter((row) => row.day === day)
                .map((row) => (
                  <li key={row.slot} style={{ ...listRowStyle, flexWrap: 'wrap' }}>
                    <strong>{SLOT_LABELS[row.slot]}</strong>
                    {slotRowLabel(row, retrySlot, pending.has(retryKey(row.day, row.slot)), target)}
                  </li>
                ))}
            </ul>
          </div>
        ))}
      </div>
      {skippedPins.length > 0 ? (
        <Banner tone={NOT_ERROR_TONE}>
          <strong>{MESSAGES.WEEK_GEN_SKIPPED_TITLE}</strong>
          <ul style={listResetStyle}>
            {skippedPins.map((pin) => (
              <li key={`${pin.day}-${pin.slot}`}>
                {MESSAGES.WEEK_GEN_SKIPPED_ITEM(DAY_LABELS[pin.day], SLOT_LABELS[pin.slot])}
              </li>
            ))}
          </ul>
        </Banner>
      ) : null}
      <Banner>{error}</Banner>
      {phase === 'finished' ? (
        <button
          type="button"
          onClick={dismiss}
          style={{ ...secondaryButtonStyle, ...target, marginTop: tokens.space.md }}
        >
          {MESSAGES.WEEK_GEN_CLOSE}
        </button>
      ) : null}
    </>
  );
}

export function WeekGenerationPanel({
  designation,
  liveWeek,
  phase,
  panelKey,
  pending = NO_PENDING,
  viewport = VIEWPORT.WIDE,
  ...generation
}) {
  const ref = useRef(null);
  useScrollIntoView(ref, panelKey);
  const isConfiguring = phase === 'configuring' || phase === 'submitting';

  return (
    <section ref={ref} style={panelStyle}>
      <h3 style={headingStyle}>{MESSAGES.WEEK_GEN_PANEL_TITLE}</h3>
      {liveWeek ? (
        <WeekLabel designation={designation} monday={liveWeek.monday} sunday={liveWeek.sunday} />
      ) : null}
      {isConfiguring ? (
        <Configuring
          {...generation}
          designation={designation}
          isSubmitting={phase === 'submitting'}
          viewport={viewport}
        />
      ) : (
        <Report {...generation} phase={phase} pending={pending} viewport={viewport} />
      )}
    </section>
  );
}

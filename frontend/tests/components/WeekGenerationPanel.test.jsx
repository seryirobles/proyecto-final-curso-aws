// @vitest-environment jsdom
// Feature 35 (T6, T7): the generation panel and its rule override editor.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, within } from '@testing-library/react';
import { WeekGenerationPanel } from '../../src/components/WeekGenerationPanel.jsx';
import { RuleOverrideEditor } from '../../src/components/RuleOverrideEditor.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { DAY_LABELS, SLOT_LABELS } from '../../src/domain/labels.js';
import { weekGridColumns } from '../../src/tokens/controlStyles.js';
import { expectTargets } from '../helpers/targets.js';

afterEach(cleanup);

const LIVE_WEEK = { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' };
const OPTIONS = {
  maxCountByCategory: { fish: 3, meat: 2 },
  daysAvailableForPin: [2],
  daysAvailableToDisable: [2, 3, 6],
};

function configuring(overrides = {}) {
  return {
    designation: 'next',
    liveWeek: LIVE_WEEK,
    phase: 'configuring',
    panelKey: '2026-W34:1',
    mode: 'mix',
    setMode: vi.fn(),
    rules: [
      { type: 'categoryCount', category: 'fish', count: 2 },
      { type: 'pin', day: 1, slot: 1, recipeId: 'r1', recipeName: 'Lentejas' },
    ],
    rulesLoading: false,
    availableOptions: OPTIONS,
    overrideDraft: null,
    startOverride: vi.fn(),
    setCategoryCount: vi.fn(),
    setDisabledDays: vi.fn(),
    submit: vi.fn(),
    close: vi.fn(),
    dismiss: vi.fn(),
    retrySlot: vi.fn(),
    pending: new Set(),
    slots: [],
    progress: { done: 0, total: 0 },
    skippedPins: [],
    error: null,
    ...overrides,
  };
}

function report(overrides = {}) {
  return configuring({
    phase: 'running',
    slots: [
      { day: 1, slot: 1, state: 'done' },
      { day: 1, slot: 2, state: 'error', message: 'La IA no ha podido.' },
      { day: 2, slot: 1, state: 'pinned' },
      { day: 2, slot: 2, state: 'running' },
    ],
    progress: { done: 2, total: 3 },
    ...overrides,
  });
}

describe('WeekGenerationPanel, configuring', () => {
  it('shows the week designation and range (R5)', () => {
    render(<WeekGenerationPanel {...configuring()} />);
    expect(screen.getByText(MESSAGES.WEEK_LABEL_NEXT)).not.toBeNull();
    expect(screen.getByText(/17\/8\/2026/)).not.toBeNull();
  });

  it('notes the current-week limit only for the current week (R6)', () => {
    render(<WeekGenerationPanel {...configuring({ designation: 'current' })} />);
    expect(screen.getByText(MESSAGES.WEEK_GEN_CURRENT_NOTE)).not.toBeNull();
    cleanup();
    render(<WeekGenerationPanel {...configuring()} />);
    expect(screen.queryByText(MESSAGES.WEEK_GEN_CURRENT_NOTE)).toBeNull();
  });

  it('states nothing existing is overwritten (R7)', () => {
    render(<WeekGenerationPanel {...configuring()} />);
    expect(screen.getByText(MESSAGES.WEEK_GEN_KEPT_NOTE)).not.toBeNull();
  });

  it('offers exactly three modes with a description each, mix checked (R8, R9, R10)', () => {
    render(<WeekGenerationPanel {...configuring()} />);
    const radios = screen.getAllByRole('radio');
    expect(radios).toHaveLength(3);
    expect(radios.map((r) => r.value)).toEqual(['library_only', 'ai_only', 'mix']);
    expect(radios.find((r) => r.checked).value).toBe('mix');
    [
      MESSAGES.WEEK_GEN_MODE_LIBRARY_HELP,
      MESSAGES.WEEK_GEN_MODE_AI_HELP,
      MESSAGES.WEEK_GEN_MODE_MIX_HELP,
    ].forEach((help) => expect(screen.getByText(help)).not.toBeNull());
    expect(screen.getByText(MESSAGES.WEEK_GEN_MODE_LEGEND).tagName).toBe('LEGEND');
  });

  it('changes the mode through the radio group', () => {
    const setMode = vi.fn();
    render(<WeekGenerationPanel {...configuring({ setMode })} />);
    fireEvent.click(screen.getAllByRole('radio')[1]);
    expect(setMode).toHaveBeenCalledWith('ai_only');
  });

  it('lists the shared rules in es-ES (R11)', () => {
    render(<WeekGenerationPanel {...configuring()} />);
    expect(screen.getByText('Pescado × 2')).not.toBeNull();
    expect(screen.getByText(`${DAY_LABELS[1]} · ${SLOT_LABELS[1]} · Lentejas`)).not.toBeNull();
  });

  it('shows a loading message while the rules load', () => {
    render(<WeekGenerationPanel {...configuring({ rulesLoading: true, rules: [] })} />);
    expect(screen.getByText(MESSAGES.WEEK_GEN_RULES_LOADING)).not.toBeNull();
  });

  it('reveals the override editors from the disclosure button (R12)', () => {
    const startOverride = vi.fn();
    render(<WeekGenerationPanel {...configuring({ startOverride })} />);
    expect(screen.queryByText(MESSAGES.WEEK_GEN_OVERRIDE_NOTE)).toBeNull();
    fireEvent.click(screen.getByText(MESSAGES.WEEK_GEN_OVERRIDE_TOGGLE));
    expect(startOverride).toHaveBeenCalled();
    cleanup();
    render(
      <WeekGenerationPanel
        {...configuring({ overrideDraft: { categoryCounts: [], disabledDays: [] } })}
      />,
    );
    expect(screen.getByText(MESSAGES.WEEK_GEN_OVERRIDE_NOTE)).not.toBeNull();
    expect(screen.queryByText(MESSAGES.WEEK_GEN_OVERRIDE_TOGGLE)).toBeNull();
  });

  it('submits and cancels from its buttons (R18)', () => {
    const submit = vi.fn();
    const close = vi.fn();
    render(<WeekGenerationPanel {...configuring({ submit, close })} />);
    fireEvent.click(screen.getByText(MESSAGES.WEEK_GEN_CONFIRM));
    fireEvent.click(screen.getByText(MESSAGES.WEEK_GEN_CANCEL));
    expect(submit).toHaveBeenCalledTimes(1);
    expect(close).toHaveBeenCalledTimes(1);
  });

  it('disables the confirm button while submitting (R21)', () => {
    render(<WeekGenerationPanel {...configuring({ phase: 'submitting' })} />);
    const button = screen.getByText(MESSAGES.WEEK_GEN_SUBMITTING);
    expect(button.disabled).toBe(true);
  });

  it('keeps a rejection in an alert banner (R22, R52)', () => {
    render(<WeekGenerationPanel {...configuring({ error: 'Reglas imposibles.' })} />);
    expect(within(screen.getByRole('alert')).getByText(/Reglas imposibles\./)).not.toBeNull();
  });

  it.each([
    ['compact', '44px'],
    ['narrow', '44px'],
    ['medium', '24px'],
    ['wide', '24px'],
  ])('gives buttons, radios and selects the target size when %s (R49)', (viewport, px) => {
    const draft = { categoryCounts: [{ category: 'fish', count: 2 }], disabledDays: [6] };
    const { container } = render(
      <WeekGenerationPanel {...configuring({ overrideDraft: draft })} viewport={viewport} />,
    );
    expectTargets(container, px);
    [...container.querySelectorAll('select, label:has(input)')].forEach((el) => {
      expect(el.style.minHeight).toBe(px);
    });
  });

  it('uses native controls only and labels every select (R51, R55)', () => {
    const { container } = render(
      <WeekGenerationPanel
        {...configuring({ overrideDraft: { categoryCounts: [], disabledDays: [] } })}
      />,
    );
    expect(container.querySelector('fieldset legend')).not.toBeNull();
    container.querySelectorAll('select').forEach((select) => {
      expect(select.closest('label')?.textContent.length).toBeGreaterThan(0);
    });
    expect(container.querySelector('[tabindex], [aria-label]')).toBeNull();
  });
});

describe('WeekGenerationPanel, report', () => {
  it('announces the done-or-error count in a status region (R27)', () => {
    render(<WeekGenerationPanel {...report()} />);
    expect(screen.getByRole('status').textContent).toBe(MESSAGES.WEEK_GEN_PROGRESS('2', '3'));
  });

  it('labels each row with the day and slot (R25)', () => {
    render(<WeekGenerationPanel {...report()} />);
    expect(screen.getByText(DAY_LABELS[1])).not.toBeNull();
    expect(screen.getByText(DAY_LABELS[2])).not.toBeNull();
    expect(screen.getAllByText(SLOT_LABELS[1])).toHaveLength(2);
  });

  it('shows pending slots as in progress, ending in an ellipsis (R26)', () => {
    render(<WeekGenerationPanel {...report()} />);
    expect(screen.getByText(MESSAGES.WEEK_GEN_SLOT_RUNNING).textContent.endsWith('…')).toBe(true);
  });

  it('shows pinned slots as filled and done slots as done (R28, R29)', () => {
    render(<WeekGenerationPanel {...report()} />);
    expect(screen.getByText(MESSAGES.WEEK_GEN_SLOT_PINNED)).not.toBeNull();
    expect(screen.getByText(MESSAGES.WEEK_GEN_SLOT_DONE)).not.toBeNull();
  });

  it('shows the error message verbatim with a retry in that row only (R34, R36)', () => {
    const retrySlot = vi.fn();
    render(<WeekGenerationPanel {...report({ retrySlot })} />);
    expect(screen.getByText('La IA no ha podido.')).not.toBeNull();
    const retry = screen.getAllByRole('button', { name: MESSAGES.WEEK_GEN_RETRY });
    expect(retry).toHaveLength(1);
    fireEvent.click(retry[0]);
    expect(retrySlot).toHaveBeenCalledWith(1, 2);
  });

  it('shows the generic message when an errored slot has none (R35)', () => {
    render(
      <WeekGenerationPanel
        {...report({ slots: [{ day: 1, slot: 1, state: 'error', message: null }] })}
      />,
    );
    expect(screen.getByText(MESSAGES.GENERIC_ERROR)).not.toBeNull();
  });

  it('offers retry on an insufficient_library_recipes row like any other (R36)', () => {
    const message = 'Faltan recetas en la biblioteca; usa el modo mixto.';
    render(
      <WeekGenerationPanel
        {...report({ slots: [{ day: 1, slot: 1, state: 'error', message }] })}
      />,
    );
    expect(screen.getByText(message)).not.toBeNull();
    expect(screen.getByRole('button', { name: MESSAGES.WEEK_GEN_RETRY })).not.toBeNull();
  });

  it('disables only the retry whose request is in flight (R39)', () => {
    render(
      <WeekGenerationPanel
        {...report({
          slots: [
            { day: 1, slot: 1, state: 'error', message: 'a' },
            { day: 1, slot: 2, state: 'error', message: 'b' },
          ],
          pending: new Set(['retry:1-2']),
        })}
      />,
    );
    const [first, second] = screen.getAllByRole('button', { name: MESSAGES.WEEK_GEN_RETRY });
    expect(first.disabled).toBe(false);
    expect(second.disabled).toBe(true);
  });

  it('reports each skipped pin with its day and slot (R31, R32)', () => {
    render(
      <WeekGenerationPanel {...report({ skippedPins: [{ day: 3, slot: 2, recipeId: 'r2' }] })} />,
    );
    expect(
      screen.getByText(MESSAGES.WEEK_GEN_SKIPPED_ITEM(DAY_LABELS[3], SLOT_LABELS[2])),
    ).not.toBeNull();
  });

  it('keeps the skipped-pin report once the run is finished (R33)', () => {
    render(
      <WeekGenerationPanel
        {...report({ phase: 'finished', skippedPins: [{ day: 3, slot: 2, recipeId: 'r2' }] })}
      />,
    );
    expect(
      screen.getByText(MESSAGES.WEEK_GEN_SKIPPED_ITEM(DAY_LABELS[3], SLOT_LABELS[2])),
    ).not.toBeNull();
  });

  it('shows a polling failure in an alert banner (R40, R52)', () => {
    render(<WeekGenerationPanel {...report({ error: 'Sin conexión.' })} />);
    expect(within(screen.getByRole('alert')).getByText(/Sin conexión\./)).not.toBeNull();
  });

  it('shows Cerrar only once the run is terminal (R41)', () => {
    const dismiss = vi.fn();
    render(<WeekGenerationPanel {...report({ dismiss })} />);
    expect(screen.queryByText(MESSAGES.WEEK_GEN_CLOSE)).toBeNull();
    cleanup();
    render(<WeekGenerationPanel {...report({ phase: 'finished', dismiss })} />);
    fireEvent.click(screen.getByText(MESSAGES.WEEK_GEN_CLOSE));
    expect(dismiss).toHaveBeenCalled();
    expect(screen.queryByRole('status')).toBeNull();
  });

  it.each([
    ['compact', 'minmax(0, 1fr)'],
    ['medium', 'repeat(4, minmax(0, 1fr))'],
    ['wide', 'repeat(7, minmax(0, 1fr))'],
  ])('uses weekGridColumns when %s (R50)', (viewport, columns) => {
    const { container } = render(<WeekGenerationPanel {...report()} viewport={viewport} />);
    expect(weekGridColumns(viewport)).toBe(columns);
    const grid = [...container.querySelectorAll('div')].find((d) => d.style.display === 'grid');
    expect(grid.style.gridTemplateColumns).toBe(columns);
  });

  it('gives retry and close the target size (R49)', () => {
    const { container } = render(
      <WeekGenerationPanel {...report({ phase: 'finished' })} viewport="compact" />,
    );
    expectTargets(container, '44px', 2);
  });

  it('sets the scroll margin to the sticky header plus day strip (R53)', () => {
    const { container } = render(<WeekGenerationPanel {...report()} />);
    expect(container.querySelector('section').style.scrollMarginTop).toBe('calc(104px)');
  });
});

describe('RuleOverrideEditor', () => {
  function editor(overrides = {}) {
    const props = {
      draft: { categoryCounts: [{ category: 'fish', count: 2 }], disabledDays: [6] },
      availableOptions: OPTIONS,
      setCategoryCount: vi.fn(),
      setDisabledDays: vi.fn(),
      ...overrides,
    };
    render(<RuleOverrideEditor {...props} />);
    return props;
  }

  it('limits counts to the API option for the chosen category (R13)', () => {
    editor();
    fireEvent.change(screen.getByLabelText(MESSAGES.RULES_CATEGORY_LABEL), {
      target: { value: 'fish' },
    });
    const count = screen.getByLabelText(MESSAGES.RULES_COUNT_LABEL);
    expect([...count.querySelectorAll('option')].map((o) => o.value)).toEqual(['', '1', '2', '3']);
  });

  it('adds a category count to the draft (R15)', () => {
    const { setCategoryCount } = editor();
    fireEvent.change(screen.getByLabelText(MESSAGES.RULES_CATEGORY_LABEL), {
      target: { value: 'meat' },
    });
    fireEvent.change(screen.getByLabelText(MESSAGES.RULES_COUNT_LABEL), { target: { value: '2' } });
    fireEvent.click(screen.getAllByText(MESSAGES.WEEK_GEN_OVERRIDE_ADD)[0]);
    expect(setCategoryCount).toHaveBeenCalledWith('meat', 2);
  });

  it('removes a draft category count', () => {
    const { setCategoryCount } = editor();
    fireEvent.click(screen.getAllByText(MESSAGES.WEEK_GEN_OVERRIDE_REMOVE)[0]);
    expect(setCategoryCount).toHaveBeenCalledWith('fish', null);
  });

  it('offers only API days not already in the draft and adds one', () => {
    const { setDisabledDays } = editor();
    const select = screen.getByLabelText(MESSAGES.RULES_DAY_LABEL);
    expect([...select.querySelectorAll('option')].map((o) => o.value)).toEqual(['', '2', '3']);
    fireEvent.change(select, { target: { value: '3' } });
    fireEvent.click(screen.getAllByText(MESSAGES.WEEK_GEN_OVERRIDE_ADD)[1]);
    expect(setDisabledDays).toHaveBeenCalledWith([3, 6]);
  });

  it('removes a draft disabled day', () => {
    const { setDisabledDays } = editor();
    fireEvent.click(screen.getAllByText(MESSAGES.WEEK_GEN_OVERRIDE_REMOVE)[1]);
    expect(setDisabledDays).toHaveBeenCalledWith([]);
  });
});

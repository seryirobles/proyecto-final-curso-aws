// @vitest-environment jsdom
// Summary -> week shortcut (frontend_ux_phase2 R60-R65).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { SummaryView } from '../../src/components/SummaryView.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { primaryButtonStyle } from '../../src/tokens/controlStyles.js';
import { tokens } from '../../src/tokens/index.js';

afterEach(cleanup);

function days(withMeal) {
  return Array.from({ length: 7 }, (_, i) => ({
    day: i + 1,
    slots: [
      {
        day: i + 1,
        slot: 1,
        candidate:
          withMeal && i === 0
            ? { id: 'c1', author: 'M', recipe: { name: 'Lentejas', category: 'legume' } }
            : null,
      },
      { day: i + 1, slot: 2, candidate: null },
    ],
  }));
}

function renderView({ withMeal = false, error, viewport, onEditWeek = vi.fn() } = {}) {
  render(
    <SummaryView
      week={{ weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' }}
      summary={{ weekId: '2026-W34', days: days(withMeal), isEmpty: !withMeal }}
      isLoading={false}
      openDetail={vi.fn()}
      detail={null}
      closeDetail={vi.fn()}
      error={error}
      viewport={viewport}
      onEditWeek={onEditWeek}
    />,
  );
  return { onEditWeek, button: screen.getByRole('button', { name: MESSAGES.SUMMARY_EDIT_WEEK }) };
}

describe('SummaryView week shortcut', () => {
  it('has the catalogue text', () => {
    expect(MESSAGES.SUMMARY_EDIT_WEEK).toBe('Editar semana');
  });

  it.each([
    ['loaded', { withMeal: true }],
    ['empty', {}],
    ['error', { error: 'No se pudo cargar.' }],
  ])('renders a native button right after the heading when %s (R60, R61)', (_n, opts) => {
    const { button } = renderView(opts);
    const heading = screen.getByText(MESSAGES.SUMMARY_VIEW_TITLE);
    expect(button.tagName).toBe('BUTTON');
    expect(button.getAttribute('type')).toBe('button');
    expect(heading.nextElementSibling).toBe(button);
  });

  it('calls onEditWeek once per click (R62)', () => {
    const { button, onEditWeek } = renderView();
    fireEvent.click(button);
    expect(onEditWeek).toHaveBeenCalledTimes(1);
  });

  it.each([
    ['compact', tokens.layout.targetMobile],
    ['narrow', tokens.layout.targetMobile],
    ['medium', tokens.layout.targetDesktop],
    ['wide', tokens.layout.targetDesktop],
  ])('has a minimum target size when %s (R63)', (viewport, size) => {
    const { button } = renderView({ viewport });
    expect(button.style.minHeight).toBe(size);
    expect(button.style.minWidth).toBe(size);
  });

  it('uses the primary button style (R64)', () => {
    const { button } = renderView();
    const probe = document.createElement('button');
    Object.assign(probe.style, primaryButtonStyle(false));
    for (const prop of ['backgroundColor', 'color', 'opacity', 'cursor', 'fontWeight']) {
      expect(button.style[prop]).toBe(probe.style[prop]);
    }
    expect(button.style.opacity).toBe('');
  });

  it('carries no aria-* attribute and no role (R65)', () => {
    const { button } = renderView();
    const names = button.getAttributeNames();
    expect(names.filter((n) => n.startsWith('aria-') || n === 'role')).toEqual([]);
  });
});

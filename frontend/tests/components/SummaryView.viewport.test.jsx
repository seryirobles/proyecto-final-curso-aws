// @vitest-environment jsdom
// Summary grid per viewport tier and empty-slot rendering (frontend_ux_phase2 R22-R25).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { SummaryView } from '../../src/components/SummaryView.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { tokens } from '../../src/tokens/index.js';
import { DAY_LABELS, SLOT_LABELS } from '../../src/domain/labels.js';

afterEach(cleanup);

function days() {
  return Array.from({ length: 7 }, (_, i) => ({
    day: i + 1,
    slots: [
      {
        day: i + 1,
        slot: 1,
        candidate:
          i === 0
            ? { id: 'c1', author: 'M', recipe: { name: 'Lentejas', category: 'legume' } }
            : null,
      },
      { day: i + 1, slot: 2, candidate: null },
    ],
  }));
}

function renderAt(viewport) {
  render(
    <SummaryView
      week={{ weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' }}
      summary={{ weekId: '2026-W34', days: days(), isEmpty: false }}
      isLoading={false}
      openDetail={vi.fn()}
      detail={null}
      closeDetail={vi.fn()}
      viewport={viewport}
    />,
  );
  return screen.getByText(DAY_LABELS[1]).parentElement.parentElement;
}

describe('SummaryView viewport layouts', () => {
  it('uses a single column when compact (R22)', () => {
    expect(renderAt('compact').style.gridTemplateColumns).toBe('1fr');
  });

  it.each(['narrow', 'medium'])('uses an auto-fill grid with summaryDayMin when %s (R23)', (vp) => {
    const columns = renderAt(vp).style.gridTemplateColumns;
    expect(columns).toContain('auto-fill');
    expect(columns).toContain(tokens.layout.summaryDayMin);
  });

  it('uses seven equal columns when wide (R24)', () => {
    expect(renderAt('wide').style.gridTemplateColumns).toBe('repeat(7, minmax(0, 1fr))');
  });

  it.each(['compact', 'narrow', 'medium', 'wide'])(
    'shows slot label then an em dash for an empty slot when %s (R25)',
    (vp) => {
      renderAt(vp);
      const dashes = screen.getAllByText(MESSAGES.SUMMARY_EMPTY_SLOT);
      expect(MESSAGES.SUMMARY_EMPTY_SLOT).toBe('—');
      expect(dashes).toHaveLength(13);
      expect(dashes[0].previousElementSibling.textContent).toBe(SLOT_LABELS[2]);
    },
  );
});

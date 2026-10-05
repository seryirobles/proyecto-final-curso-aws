// @vitest-environment jsdom
// Touch targets in the non-week views (frontend_ux_phase2 R42-R44).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import { SummaryView } from '../../src/components/SummaryView.jsx';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';
import { RulesView } from '../../src/components/RulesView.jsx';
import { LibraryView } from '../../src/components/LibraryView.jsx';
import { AccountRow } from '../../src/components/AccountRow.jsx';
import { expectTargets } from '../helpers/targets.js';

afterEach(cleanup);

const noop = vi.fn();
const CONFIRM = { pending: null, confirm: noop, cancel: noop };
const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function summary(viewport) {
  const days = [
    {
      day: 1,
      slots: [
        { day: 1, slot: 1, candidate: { id: 'c1', author: 'M', recipe: { name: 'Lentejas' } } },
      ],
    },
  ];
  return render(
    <SummaryView
      week={{ weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' }}
      summary={{ weekId: '2026-W34', days, isEmpty: false }}
      isLoading={false}
      openDetail={noop}
      detail={null}
      closeDetail={noop}
      viewport={viewport}
    />,
  );
}

function shopping(viewport) {
  const item = (id, checked) => ({ id, name: 'arroz', quantity: 5, unit: 'g', checked });
  return render(
    <ShoppingListView
      uncheckedItems={[item('a', false)]}
      checkedItems={[item('b', true)]}
      isLoading={false}
      liveWeeks={LIVE_WEEKS}
      isFormOpen
      isEditing={false}
      draft={{ name: '', quantity: '', unit: '' }}
      updateDraftField={noop}
      canSaveItem={false}
      openAdd={noop}
      openEdit={noop}
      closeForm={noop}
      saveItem={noop}
      setChecked={noop}
      remove={noop}
      confirm={CONFIRM}
      isResyncing={false}
      resync={noop}
      error={null}
      viewport={viewport}
    />,
  );
}

function rules(viewport) {
  return render(
    <RulesView
      categoryCounts={[{ category: 'meat', count: 1 }]}
      pins={[]}
      disabledDays={[1]}
      isLoading={false}
      error={null}
      confirm={CONFIRM}
      remove={noop}
      picker={{
        filters: { name: '', category: '' },
        setName: noop,
        setCategory: noop,
        recipes: [{ id: 'r-1', name: 'Lentejas', category: 'legume', author: 'Marta' }],
        allRecipes: [],
        isLoading: false,
        connectionLost: false,
      }}
      categoryCountDraft={{ category: '', count: '' }}
      categoryCountOptions={[]}
      setCategoryCountCategory={noop}
      setCategoryCountCount={noop}
      canSaveCategoryCount={false}
      saveCategoryCount={noop}
      pinDraft={{ day: '', slot: '' }}
      pinDayOptions={[]}
      setPinDay={noop}
      setPinSlot={noop}
      pinRecipeId={null}
      selectPinRecipe={noop}
      canSavePin={false}
      savePin={noop}
      disabledDayDraft={{ day: '' }}
      disabledDayOptions={[]}
      setDisabledDayDay={noop}
      canSaveDisabledDay={false}
      saveDisabledDay={noop}
      viewport={viewport}
    />,
  );
}

function library(viewport) {
  return render(
    <LibraryView
      recipes={[{ id: 'r-1', name: 'Lentejas', category: 'legume', author: 'Marta' }]}
      filters={{ name: '', category: '' }}
      setName={noop}
      setCategory={noop}
      isLoading={false}
      isAuthoringOpen={false}
      authoring={{}}
      openAdd={noop}
      openEdit={noop}
      closeAuthoring={noop}
      remove={noop}
      confirm={CONFIRM}
      openDetail={noop}
      detail={null}
      detailError={null}
      closeDetail={noop}
      error={null}
      viewport={viewport}
    />,
  );
}

function row(viewport, overrides) {
  return render(
    <AccountRow
      account={{ userId: 'u-1', username: 'ana', role: 'User', passwordResetRequired: false }}
      actingUserId="admin-1"
      isRenaming={false}
      renameDraft=""
      onRenameDraftChange={noop}
      canSaveRename={false}
      onOpenRename={noop}
      onSaveRename={noop}
      onCancelRename={noop}
      isResetting={false}
      resetDraft=""
      onResetDraftChange={noop}
      canSaveReset={false}
      onOpenReset={noop}
      onSaveReset={noop}
      onCancelReset={noop}
      onRemove={noop}
      viewport={viewport}
      {...overrides}
    />,
  );
}

describe.each([
  ['compact', '44px'],
  ['narrow', '44px'],
  ['medium', '24px'],
  ['wide', '24px'],
])('buttons when %s', (viewport, px) => {
  it('SummaryView recipe link', () => {
    expectTargets(summary(viewport).container, px, 1);
  });

  it('ShoppingListView (rows, resync, add, form)', () => {
    expectTargets(shopping(viewport).container, px);
  });

  it('RulesView', () => {
    expectTargets(rules(viewport).container, px);
  });

  it('LibraryView', () => {
    expectTargets(library(viewport).container, px);
  });

  it('AccountRow (plain, renaming, resetting)', () => {
    expectTargets(row(viewport).container, px);
    cleanup();
    expectTargets(row(viewport, { isRenaming: true }).container, px);
    cleanup();
    expectTargets(row(viewport, { isResetting: true }).container, px);
  });
});

describe('shopping rows (R44)', () => {
  it.each([
    ['compact', '48px'],
    ['narrow', '48px'],
    ['medium', ''],
    ['wide', ''],
  ])('item row min height when %s', (viewport, minHeight) => {
    const rows = [...shopping(viewport).container.querySelectorAll('li')];
    expect(rows).toHaveLength(2);
    rows.forEach((li) => expect(li.style.minHeight).toBe(minHeight));
  });
});

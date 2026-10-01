// @vitest-environment jsdom
// R2: quantities render through formatNumber (es-ES decimal comma).
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { ShoppingListView } from '../../src/components/ShoppingListView.jsx';

afterEach(cleanup);

const noop = vi.fn();
const props = {
  uncheckedItems: [{ id: 's-1', name: 'aceite', quantity: 0.5, unit: 'l', checked: false }],
  checkedItems: [],
  isLoading: false,
  liveWeeks: null,
  isFormOpen: false,
  isEditing: false,
  draft: { name: '', quantity: '', unit: '' },
  updateDraftField: noop,
  canSaveItem: false,
  openAdd: noop,
  openEdit: noop,
  closeForm: noop,
  saveItem: noop,
  setChecked: noop,
  remove: noop,
  confirm: { pending: null, confirm: noop, cancel: noop },
  isResyncing: false,
  resync: noop,
  error: null,
};

describe('ShoppingListView quantity format', () => {
  it('renders 0.5 as "0,5" (R2)', () => {
    render(<ShoppingListView {...props} />);

    expect(screen.getByText(/aceite · 0,5 /)).not.toBeNull();
  });
});

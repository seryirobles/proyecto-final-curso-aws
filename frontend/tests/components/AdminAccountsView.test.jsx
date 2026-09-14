// @vitest-environment jsdom
// T57 (R19, R20, R33, R35): loading/empty states, the create form's exactly
// two fields (no role selector), a fixture list renders one row per account.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { AdminAccountsView } from '../../src/components/AdminAccountsView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

function account(userId, overrides = {}) {
  return {
    userId,
    username: `user-${userId}`,
    role: 'User',
    passwordResetRequired: false,
    ...overrides,
  };
}

function baseProps(overrides = {}) {
  return {
    accounts: [],
    isLoading: false,
    error: null,
    actingUserId: 'admin-1',
    newUsername: '',
    setNewUsername: vi.fn(),
    newTemporaryPassword: '',
    setNewTemporaryPassword: vi.fn(),
    canCreate: false,
    create: vi.fn(),
    renamingId: null,
    renameDraft: '',
    setRenameDraft: vi.fn(),
    canSaveRename: false,
    openRename: vi.fn(),
    saveRename: vi.fn(),
    cancelRename: vi.fn(),
    resettingId: null,
    resetDraft: '',
    setResetDraft: vi.fn(),
    canSaveReset: false,
    openReset: vi.fn(),
    saveReset: vi.fn(),
    cancelReset: vi.fn(),
    remove: vi.fn(),
    confirm: { pending: null, confirm: vi.fn(), cancel: vi.fn() },
    ...overrides,
  };
}

describe('AdminAccountsView', () => {
  it('renders LoadingState while isLoading (R20)', () => {
    render(<AdminAccountsView {...baseProps({ isLoading: true })} />);

    expect(screen.getByText(MESSAGES.LOADING_STATE_DEFAULT)).not.toBeNull();
  });

  it('renders EmptyState with zero accounts (R19)', () => {
    render(<AdminAccountsView {...baseProps({ accounts: [] })} />);

    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_VIEW_EMPTY)).not.toBeNull();
  });

  it('the create form has exactly two input fields, neither a role selector (R35)', () => {
    const { container } = render(<AdminAccountsView {...baseProps()} />);

    const inputs = container.querySelectorAll('input');
    expect(container.querySelectorAll('select')).toHaveLength(0);
    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_NEW_USERNAME_LABEL)).not.toBeNull();
    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_TEMP_PASSWORD_LABEL)).not.toBeNull();
    // Only the two create-form fields exist when the list is empty.
    expect(inputs).toHaveLength(2);
  });

  it('renders one row per account in the fixture list (R33)', () => {
    render(
      <AdminAccountsView
        {...baseProps({
          accounts: [account('u-1', { username: 'ana' }), account('u-2', { username: 'bea' })],
        })}
      />,
    );

    expect(screen.getByText('ana')).not.toBeNull();
    expect(screen.getByText('bea')).not.toBeNull();
  });

  it('renders the create control disabled until canCreate is true', () => {
    render(<AdminAccountsView {...baseProps({ canCreate: false })} />);

    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_CREATE).closest('button').disabled).toBe(true);
  });
});

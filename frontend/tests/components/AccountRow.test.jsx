// @vitest-environment jsdom
// T57 (R33, R34, R36, R37): username/role/pending badge; rename/reset/remove
// controls; reset hidden on the acting admin's own row; remove hidden on an
// admin-role row.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { AccountRow } from '../../src/components/AccountRow.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

function account(overrides = {}) {
  return {
    userId: 'u-1',
    username: 'ana',
    role: 'User',
    passwordResetRequired: false,
    ...overrides,
  };
}

function baseProps(overrides = {}) {
  return {
    account: account(),
    actingUserId: 'admin-1',
    isRenaming: false,
    renameDraft: '',
    onRenameDraftChange: vi.fn(),
    canSaveRename: false,
    onOpenRename: vi.fn(),
    onSaveRename: vi.fn(),
    onCancelRename: vi.fn(),
    isResetting: false,
    resetDraft: '',
    onResetDraftChange: vi.fn(),
    canSaveReset: false,
    onOpenReset: vi.fn(),
    onSaveReset: vi.fn(),
    onCancelReset: vi.fn(),
    onRemove: vi.fn(),
    ...overrides,
  };
}

describe('AccountRow', () => {
  it('renders username, role label, and a pending badge when a reset is required (R33)', () => {
    render(<AccountRow {...baseProps({ account: account({ passwordResetRequired: true }) })} />);

    expect(screen.getByText('ana')).not.toBeNull();
    expect(screen.getByText('Usuario')).not.toBeNull();
    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_PENDING_BADGE)).not.toBeNull();
  });

  it('renders no pending badge when a reset is not required', () => {
    render(<AccountRow {...baseProps({ account: account({ passwordResetRequired: false }) })} />);

    expect(screen.queryByText(MESSAGES.ADMIN_ACCOUNTS_PENDING_BADGE)).toBeNull();
  });

  it('renders rename, reset and remove controls for an ordinary row (R34)', () => {
    render(<AccountRow {...baseProps()} />);

    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_RENAME)).not.toBeNull();
    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD)).not.toBeNull();
    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_REMOVE)).not.toBeNull();
  });

  it("hides the reset-password control on the acting admin's own row (R37)", () => {
    render(
      <AccountRow
        {...baseProps({ account: account({ userId: 'admin-1' }), actingUserId: 'admin-1' })}
      />,
    );

    expect(screen.queryByText(MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD)).toBeNull();
    // The row is not disabled wholesale - rename/remove still render (mutation
    // guard: a swapped condition could hide everything and still "pass").
    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_RENAME)).not.toBeNull();
    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_REMOVE)).not.toBeNull();
  });

  it('hides reset-password on every row when actingUserId is not yet known (R37 fail-closed)', () => {
    render(
      <AccountRow
        {...baseProps({ account: account({ userId: 'someone-else' }), actingUserId: undefined })}
      />,
    );

    expect(screen.queryByText(MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD)).toBeNull();
  });

  it('shows the reset-password control on a row that is NOT the acting admin (R37 boundary)', () => {
    render(
      <AccountRow
        {...baseProps({ account: account({ userId: 'someone-else' }), actingUserId: 'admin-1' })}
      />,
    );

    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD)).not.toBeNull();
  });

  it('hides the remove control on an admin-role row (R36)', () => {
    render(
      <AccountRow {...baseProps({ account: account({ role: 'Admin', userId: 'other-admin' }) })} />,
    );

    expect(screen.queryByText(MESSAGES.ADMIN_ACCOUNTS_REMOVE)).toBeNull();
    // Again, only remove is hidden - not the whole row's controls.
    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_RENAME)).not.toBeNull();
  });

  it('shows the remove control on a User-role row (R36 boundary)', () => {
    render(<AccountRow {...baseProps({ account: account({ role: 'User' }) })} />);

    expect(screen.getByText(MESSAGES.ADMIN_ACCOUNTS_REMOVE)).not.toBeNull();
  });
});

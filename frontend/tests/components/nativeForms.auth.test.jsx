// @vitest-environment jsdom
// R15-R21, R25, R28-R30: native forms on login, set-password and admin.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { tokens } from '../../src/tokens/index.js';
import { MESSAGES } from '../../src/messages/index.js';
import { primaryButtonStyle } from '../../src/tokens/controlStyles.js';
import { LoginView } from '../../src/components/LoginView.jsx';
import { SetPasswordView } from '../../src/components/SetPasswordView.jsx';
import { AdminAccountsView } from '../../src/components/AdminAccountsView.jsx';
import { AccountRow } from '../../src/components/AccountRow.jsx';

afterEach(cleanup);

const noop = vi.fn();

function loginProps(overrides = {}) {
  return {
    username: '',
    setUsername: noop,
    password: '',
    setPassword: noop,
    canSubmit: true,
    submit: vi.fn(),
    error: null,
    isSubmitting: false,
    ...overrides,
  };
}

function setPasswordProps(overrides = {}) {
  return {
    status: 'passwordResetPending',
    newPassword: '',
    setNewPassword: noop,
    confirmPassword: '',
    setConfirmPassword: noop,
    mismatch: false,
    canSubmit: true,
    submit: vi.fn(),
    cancel: noop,
    error: null,
    isSubmitting: false,
    ...overrides,
  };
}

function adminProps(overrides = {}) {
  return {
    accounts: [],
    isLoading: false,
    error: null,
    actingUserId: 'a',
    newUsername: '',
    setNewUsername: noop,
    newTemporaryPassword: '',
    setNewTemporaryPassword: noop,
    canCreate: true,
    create: vi.fn(),
    confirm: { pending: null, confirm: noop, cancel: noop },
    ...overrides,
  };
}

function rowProps(overrides = {}) {
  return {
    account: { userId: 'u-1', username: 'ana', role: 'User', passwordResetRequired: false },
    actingUserId: 'admin-1',
    isRenaming: false,
    renameDraft: '',
    onRenameDraftChange: noop,
    canSaveRename: true,
    onOpenRename: noop,
    onSaveRename: vi.fn(),
    onCancelRename: noop,
    isResetting: false,
    resetDraft: '',
    onResetDraftChange: noop,
    canSaveReset: true,
    onOpenReset: noop,
    onSaveReset: vi.fn(),
    onCancelReset: noop,
    onRemove: noop,
    ...overrides,
  };
}

describe('disabled submit look', () => {
  it('a disabled primary button has reduced opacity and not-allowed cursor (R30)', () => {
    expect(tokens.opacity.disabled).toBe(0.55);
    expect(primaryButtonStyle(true).opacity).toBe(tokens.opacity.disabled);
    expect(primaryButtonStyle(true).cursor).toBe('not-allowed');
    expect(primaryButtonStyle(false).opacity).toBeUndefined();
  });
});

describe('LoginView form', () => {
  it('submits through the form, ignoring it when disabled (R15, R25)', () => {
    const submit = vi.fn();
    const { container, rerender } = render(<LoginView {...loginProps({ submit })} />);

    fireEvent.submit(container.querySelector('form'));
    expect(submit).toHaveBeenCalledTimes(1);

    rerender(<LoginView {...loginProps({ submit, canSubmit: false })} />);
    fireEvent.submit(container.querySelector('form'));
    expect(submit).toHaveBeenCalledTimes(1);
  });

  it('sets name, autocomplete, spellcheck and capitalisation attributes (R16)', () => {
    render(<LoginView {...loginProps()} />);

    const user = screen.getByLabelText(MESSAGES.LOGIN_USERNAME_LABEL);
    const pass = screen.getByLabelText(MESSAGES.LOGIN_PASSWORD_LABEL);
    expect(user.getAttribute('autocomplete')).toBe('username');
    expect(user.getAttribute('spellcheck')).toBe('false');
    expect(user.getAttribute('autocapitalize')).toBe('none');
    expect(user.getAttribute('name')).toBe('username');
    expect(pass.getAttribute('autocomplete')).toBe('current-password');
    expect(pass.getAttribute('name')).toBe('password');
  });

  it('shows the busy label and the disabled look while submitting (R28, R30)', () => {
    render(<LoginView {...loginProps({ isSubmitting: true })} />);

    const button = screen.getByText(MESSAGES.LOGIN_SUBMITTING);
    expect(MESSAGES.LOGIN_SUBMITTING).toBe('Entrando…');
    expect(button.disabled).toBe(true);
    expect(button.style.opacity).toBe(String(tokens.opacity.disabled));
    expect(button.style.cursor).toBe('not-allowed');
  });
});

describe('SetPasswordView form', () => {
  it('submits through the form, ignoring it when disabled (R17, R25)', () => {
    const submit = vi.fn();
    const { container, rerender } = render(<SetPasswordView {...setPasswordProps({ submit })} />);

    fireEvent.submit(container.querySelector('form'));
    expect(submit).toHaveBeenCalledTimes(1);

    rerender(<SetPasswordView {...setPasswordProps({ submit, canSubmit: false })} />);
    fireEvent.submit(container.querySelector('form'));
    expect(submit).toHaveBeenCalledTimes(1);
  });

  it('names both inputs and marks them new-password (R18)', () => {
    const { container } = render(<SetPasswordView {...setPasswordProps()} />);

    const inputs = container.querySelectorAll('input');
    expect(inputs).toHaveLength(2);
    inputs.forEach((el) => {
      expect(el.getAttribute('autocomplete')).toBe('new-password');
      expect(el.getAttribute('name')).toBeTruthy();
    });
  });

  it('shows the busy label while submitting and keeps cancel a plain button (R29, R27)', () => {
    render(<SetPasswordView {...setPasswordProps({ isSubmitting: true })} />);

    expect(screen.getByText(MESSAGES.SET_PASSWORD_SUBMITTING)).not.toBeNull();
    expect(MESSAGES.SET_PASSWORD_SUBMITTING).toBe('Guardando…');
    expect(screen.getByText(MESSAGES.SET_PASSWORD_CANCEL).getAttribute('type')).toBe('button');
  });
});

describe('Admin forms', () => {
  it('create form submits through the form and sets autocomplete attributes (R19, R20, R25)', () => {
    const create = vi.fn();
    const { container, rerender } = render(<AdminAccountsView {...adminProps({ create })} />);

    fireEvent.submit(container.querySelector('form'));
    expect(create).toHaveBeenCalledTimes(1);

    const user = screen.getByLabelText(MESSAGES.ADMIN_ACCOUNTS_NEW_USERNAME_LABEL);
    const pass = screen.getByLabelText(MESSAGES.ADMIN_ACCOUNTS_TEMP_PASSWORD_LABEL);
    expect(user.getAttribute('autocomplete')).toBe('off');
    expect(user.getAttribute('spellcheck')).toBe('false');
    expect(user.getAttribute('autocapitalize')).toBe('none');
    expect(pass.getAttribute('autocomplete')).toBe('new-password');

    rerender(<AdminAccountsView {...adminProps({ create, canCreate: false })} />);
    fireEvent.submit(container.querySelector('form'));
    expect(create).toHaveBeenCalledTimes(1);
  });

  it('AccountRow rename and reset inputs sit in forms that submit (R21)', () => {
    const onSaveRename = vi.fn();
    const rename = render(<AccountRow {...rowProps({ isRenaming: true, onSaveRename })} />);
    fireEvent.submit(rename.container.querySelector('input').closest('form'));
    expect(onSaveRename).toHaveBeenCalledTimes(1);
    cleanup();

    const onSaveReset = vi.fn();
    const reset = render(<AccountRow {...rowProps({ isResetting: true, onSaveReset })} />);
    const input = reset.container.querySelector('input');
    expect(input.getAttribute('autocomplete')).toBe('new-password');
    fireEvent.submit(input.closest('form'));
    expect(onSaveReset).toHaveBeenCalledTimes(1);
  });
});

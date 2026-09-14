// @vitest-environment jsdom
// T53 (R26): renders only while status === "passwordResetPending"; new +
// confirm fields, mismatch copy, inline error, Cancelar control.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { SetPasswordView } from '../../src/components/SetPasswordView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

function baseProps(overrides = {}) {
  return {
    status: 'passwordResetPending',
    newPassword: '',
    setNewPassword: vi.fn(),
    confirmPassword: '',
    setConfirmPassword: vi.fn(),
    mismatch: false,
    canSubmit: false,
    submit: vi.fn(),
    cancel: vi.fn(),
    error: null,
    isSubmitting: false,
    ...overrides,
  };
}

describe('SetPasswordView', () => {
  it('renders nothing outside passwordResetPending (R26)', () => {
    const { container } = render(<SetPasswordView {...baseProps({ status: 'authenticated' })} />);

    expect(container.firstChild).toBeNull();
  });

  it('renders new-password, confirm and Cancelar while pending (R26)', () => {
    render(<SetPasswordView {...baseProps()} />);

    // getByLabelText, not getByText - the title and the field label share
    // copy ("Nueva contraseña"); the label/input pairing disambiguates.
    expect(screen.getByLabelText(MESSAGES.SET_PASSWORD_NEW_LABEL)).not.toBeNull();
    expect(screen.getByLabelText(MESSAGES.SET_PASSWORD_CONFIRM_LABEL)).not.toBeNull();
    expect(screen.getByText(MESSAGES.SET_PASSWORD_CANCEL)).not.toBeNull();
  });

  it('masks both password fields (security-relevant: type="password")', () => {
    render(<SetPasswordView {...baseProps()} />);

    expect(screen.getByLabelText(MESSAGES.SET_PASSWORD_NEW_LABEL).type).toBe('password');
    expect(screen.getByLabelText(MESSAGES.SET_PASSWORD_CONFIRM_LABEL).type).toBe('password');
  });

  it('renders the mismatch copy only when mismatch is true', () => {
    const { rerender } = render(<SetPasswordView {...baseProps({ mismatch: false })} />);
    expect(screen.queryByText(MESSAGES.SET_PASSWORD_MISMATCH)).toBeNull();

    rerender(<SetPasswordView {...baseProps({ mismatch: true })} />);
    expect(screen.getByText(MESSAGES.SET_PASSWORD_MISMATCH)).not.toBeNull();
  });

  it('renders a caught PASSWORD_TOO_SHORT detail inline', () => {
    render(
      <SetPasswordView
        {...baseProps({ error: 'La contraseña debe tener al menos 10 caracteres.' })}
      />,
    );

    expect(screen.getByText('La contraseña debe tener al menos 10 caracteres.')).not.toBeNull();
  });

  it('the submit control is disabled while canSubmit is false', () => {
    render(<SetPasswordView {...baseProps({ canSubmit: false })} />);

    expect(screen.getByText(MESSAGES.SET_PASSWORD_SUBMIT).closest('button').disabled).toBe(true);
  });
});

// @vitest-environment jsdom
// T53 (R26, R27): status pass-through, submit calls session.setPassword with
// the new password, a mismatched confirm blocks submit, PASSWORD_TOO_SHORT
// renders its detail, Cancelar calls session.logout.
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../src/api/client.js';
import { useSetPasswordForm } from '../../src/hooks/useSetPasswordForm.js';

function fakeSession({ status = 'passwordResetPending', setPasswordImpl } = {}) {
  return {
    session: { status },
    setPassword: vi.fn(setPasswordImpl),
    logout: vi.fn(),
  };
}

describe('useSetPasswordForm', () => {
  it('passes the session status through as-is (R26)', () => {
    const { result: pending } = renderHook(() =>
      useSetPasswordForm(fakeSession({ status: 'passwordResetPending' })),
    );
    expect(pending.current.status).toBe('passwordResetPending');

    const { result: authenticated } = renderHook(() =>
      useSetPasswordForm(fakeSession({ status: 'authenticated' })),
    );
    expect(authenticated.current.status).toBe('authenticated');
  });

  it('submit calls session.setPassword with the entered new password (R27)', async () => {
    const session = fakeSession({ setPasswordImpl: () => Promise.resolve() });
    const { result } = renderHook(() => useSetPasswordForm(session));
    act(() => result.current.setNewPassword('correct horse battery staple'));
    act(() => result.current.setConfirmPassword('correct horse battery staple'));

    await act(async () => result.current.submit());

    expect(session.setPassword).toHaveBeenCalledWith('correct horse battery staple');
  });

  it('a mismatched confirm field blocks submit', async () => {
    const session = fakeSession({ setPasswordImpl: () => Promise.resolve() });
    const { result } = renderHook(() => useSetPasswordForm(session));
    act(() => result.current.setNewPassword('correct horse battery staple'));
    act(() => result.current.setConfirmPassword('something else entirely'));

    expect(result.current.mismatch).toBe(true);
    expect(result.current.canSubmit).toBe(false);
    await act(async () => result.current.submit());
    expect(session.setPassword).not.toHaveBeenCalled();
  });

  it('a matching confirm field does not report a mismatch', () => {
    const { result } = renderHook(() => useSetPasswordForm(fakeSession()));
    act(() => result.current.setNewPassword('correct horse battery staple'));
    act(() => result.current.setConfirmPassword('correct horse battery staple'));

    expect(result.current.mismatch).toBe(false);
    expect(result.current.canSubmit).toBe(true);
  });

  it('a caught PASSWORD_TOO_SHORT ApiError renders its detail', async () => {
    const detail = 'La contraseña debe tener al menos 10 caracteres.';
    const session = fakeSession({
      setPasswordImpl: () =>
        Promise.reject(new ApiError({ status: 422, code: 'PASSWORD_TOO_SHORT', detail })),
    });
    const { result } = renderHook(() => useSetPasswordForm(session));
    act(() => result.current.setNewPassword('short'));
    act(() => result.current.setConfirmPassword('short'));

    await act(async () => result.current.submit());

    expect(result.current.error).toBe(detail);
  });

  it('cancel calls session.logout', () => {
    const session = fakeSession();
    const { result } = renderHook(() => useSetPasswordForm(session));

    act(() => result.current.cancel());

    expect(session.logout).toHaveBeenCalled();
  });
});

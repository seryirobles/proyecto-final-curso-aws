// @vitest-environment jsdom
// T51 (R24, R25, R29): draft fields, submit calls session.login with the
// entered values, a caught INVALID_CREDENTIALS renders inline.
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../src/api/client.js';
import { useLoginForm } from '../../src/hooks/useLoginForm.js';

function fakeSession(loginImpl) {
  return { login: vi.fn(loginImpl) };
}

describe('useLoginForm', () => {
  it('starts with empty username/password and submit disabled', () => {
    const { result } = renderHook(() => useLoginForm(fakeSession()));

    expect(result.current.username).toBe('');
    expect(result.current.password).toBe('');
    expect(result.current.canSubmit).toBe(false);
  });

  it('submit calls session.login with the entered username and password (R25)', async () => {
    const session = fakeSession(() => Promise.resolve());
    const { result } = renderHook(() => useLoginForm(session));

    act(() => result.current.setUsername('marta'));
    act(() => result.current.setPassword('s3cret!!!'));
    await act(async () => result.current.submit());

    expect(session.login).toHaveBeenCalledWith('marta', 's3cret!!!');
  });

  it('does not call session.login while a field is empty', async () => {
    const session = fakeSession(() => Promise.resolve());
    const { result } = renderHook(() => useLoginForm(session));
    act(() => result.current.setUsername('marta'));

    await act(async () => result.current.submit());

    expect(session.login).not.toHaveBeenCalled();
  });

  it('a caught INVALID_CREDENTIALS ApiError sets error to its detail', async () => {
    const detail = 'Usuario o contraseña incorrectos.';
    const session = fakeSession(() =>
      Promise.reject(new ApiError({ status: 401, code: 'INVALID_CREDENTIALS', detail })),
    );
    const { result } = renderHook(() => useLoginForm(session));
    act(() => result.current.setUsername('marta'));
    act(() => result.current.setPassword('wrong'));

    await act(async () => result.current.submit());

    expect(result.current.error).toBe(detail);
  });

  it('a successful submit clears any previous error', async () => {
    const session = fakeSession();
    session.login
      .mockRejectedValueOnce(
        new ApiError({ status: 401, code: 'INVALID_CREDENTIALS', detail: 'x' }),
      )
      .mockResolvedValueOnce();
    const { result } = renderHook(() => useLoginForm(session));
    act(() => result.current.setUsername('marta'));
    act(() => result.current.setPassword('wrong'));
    await act(async () => result.current.submit());
    expect(result.current.error).toBe('x');

    await act(async () => result.current.submit());

    expect(result.current.error).toBeNull();
  });
});

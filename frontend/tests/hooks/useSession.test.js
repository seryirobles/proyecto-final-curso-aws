// @vitest-environment jsdom
// T47 (R23, R25, R26, R27, R32): every mount-time probe outcome, login's two
// branches by passwordResetRequired, setPassword's re-probe, logout's reset.
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch, ApiError } from '../../src/api/client.js';
import { useSession } from '../../src/hooks/useSession.js';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function sessionExpired() {
  return new ApiError({ status: 401, code: 'SESSION_EXPIRED', detail: 'x' });
}

describe('useSession', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it('probe 200 resolves authenticated User (R23)', async () => {
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    const { result } = renderHook(() => useSession());

    await waitFor(() =>
      expect(result.current.session).toEqual({ status: 'authenticated', role: 'User' }),
    );
  });

  it('probe FORBIDDEN resolves authenticated Admin (R23)', async () => {
    apiFetch.mockRejectedValue(new ApiError({ status: 403, code: 'FORBIDDEN', detail: 'x' }));
    const { result } = renderHook(() => useSession());

    await waitFor(() =>
      expect(result.current.session).toEqual({ status: 'authenticated', role: 'Admin' }),
    );
  });

  it('probe PASSWORD_RESET_PENDING resolves passwordResetPending (R23)', async () => {
    apiFetch.mockRejectedValue(
      new ApiError({ status: 403, code: 'PASSWORD_RESET_PENDING', detail: 'x' }),
    );
    const { result } = renderHook(() => useSession());

    await waitFor(() => expect(result.current.session).toEqual({ status: 'passwordResetPending' }));
  });

  it('probe SESSION_EXPIRED resolves anonymous (R23)', async () => {
    apiFetch.mockRejectedValue(sessionExpired());
    const { result } = renderHook(() => useSession());

    await waitFor(() => expect(result.current.session).toEqual({ status: 'anonymous' }));
  });

  it('any other probe rejection also resolves anonymous, never stays loading (R23)', async () => {
    apiFetch.mockRejectedValue(new ApiError({ status: 0, code: 'NETWORK_ERROR', detail: 'x' }));
    const { result } = renderHook(() => useSession());

    await waitFor(() => expect(result.current.session).toEqual({ status: 'anonymous' }));
  });

  it('login with passwordResetRequired true routes to passwordResetPending, not the returned role (R25, R26)', async () => {
    apiFetch.mockImplementation((url) =>
      url === '/v1/session'
        ? Promise.resolve({ role: 'User', passwordResetRequired: true })
        : Promise.reject(sessionExpired()),
    );
    const { result } = renderHook(() => useSession());
    await waitFor(() => expect(result.current.session.status).toBe('anonymous'));

    await act(async () => result.current.login('ana', 'secret'));

    expect(apiFetch).toHaveBeenCalledWith('/v1/session', {
      method: 'POST',
      body: { username: 'ana', password: 'secret' },
    });
    expect(result.current.session).toEqual({ status: 'passwordResetPending' });
  });

  it('login with passwordResetRequired false authenticates with the returned role (R25)', async () => {
    apiFetch.mockImplementation((url) =>
      url === '/v1/session'
        ? Promise.resolve({ role: 'Admin', passwordResetRequired: false })
        : Promise.reject(sessionExpired()),
    );
    const { result } = renderHook(() => useSession());
    await waitFor(() => expect(result.current.session.status).toBe('anonymous'));

    await act(async () => result.current.login('admin', 'secret'));

    expect(result.current.session).toEqual({ status: 'authenticated', role: 'Admin' });
  });

  it('login also carries the response userId through (R37 - AdminAccountsView self-row)', async () => {
    apiFetch.mockImplementation((url) =>
      url === '/v1/session'
        ? Promise.resolve({ userId: 'admin-1', role: 'Admin', passwordResetRequired: false })
        : Promise.reject(sessionExpired()),
    );
    const { result } = renderHook(() => useSession());
    await waitFor(() => expect(result.current.session.status).toBe('anonymous'));

    await act(async () => result.current.login('admin', 'secret'));

    expect(result.current.session).toEqual({
      status: 'authenticated',
      role: 'Admin',
      userId: 'admin-1',
    });
  });

  it('setPassword PUTs the new password then re-probes live-weeks (R27)', async () => {
    let probeCount = 0;
    apiFetch.mockImplementation((url) => {
      if (url === '/v1/live-weeks') {
        probeCount += 1;
        return probeCount === 1
          ? Promise.reject(
              new ApiError({ status: 403, code: 'PASSWORD_RESET_PENDING', detail: 'x' }),
            )
          : Promise.resolve(LIVE_WEEKS);
      }
      return Promise.resolve(null);
    });
    const { result } = renderHook(() => useSession());
    await waitFor(() => expect(result.current.session).toEqual({ status: 'passwordResetPending' }));

    await act(async () => result.current.setPassword('correct horse battery staple'));

    expect(apiFetch).toHaveBeenCalledWith('/v1/session/password', {
      method: 'PUT',
      body: { newPassword: 'correct horse battery staple' },
    });
    expect(probeCount).toBe(2);
    expect(result.current.session).toEqual({ status: 'authenticated', role: 'User' });
  });

  it('logout DELETEs the session and resets to anonymous regardless of prior role (R32)', async () => {
    apiFetch.mockImplementation((url) =>
      url === '/v1/live-weeks' ? Promise.resolve(LIVE_WEEKS) : Promise.resolve(null),
    );
    const { result } = renderHook(() => useSession());
    await waitFor(() => expect(result.current.session.status).toBe('authenticated'));

    await act(async () => result.current.logout());

    expect(apiFetch).toHaveBeenCalledWith('/v1/session', { method: 'DELETE' });
    expect(result.current.session).toEqual({ status: 'anonymous' });
  });
});

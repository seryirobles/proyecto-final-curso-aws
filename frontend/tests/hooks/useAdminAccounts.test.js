// @vitest-environment jsdom
// T57 (R18, R35): GET on mount, create/rename/reset/remove wiring, refetch
// after every mutation. See progress/impl_frontend_spa.md -> "Auth screens,
// second half".
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch } from '../../src/api/client.js';
import { useAdminAccounts } from '../../src/hooks/useAdminAccounts.js';

function account(userId, overrides = {}) {
  return {
    userId,
    username: 'ana',
    role: 'User',
    passwordResetRequired: false,
    ...overrides,
  };
}

describe('useAdminAccounts', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it('GETs /v1/users on mount, not through usePolling (design.md section 5a)', async () => {
    apiFetch.mockResolvedValue({ users: [account('u-1')] });
    const { result } = renderHook(() => useAdminAccounts());

    await waitFor(() => expect(result.current.accounts).toHaveLength(1));
    expect(apiFetch).toHaveBeenCalledWith('/v1/users');
  });

  it('does not fetch at all while active: false', () => {
    apiFetch.mockResolvedValue({ users: [] });
    renderHook(() => useAdminAccounts({ active: false }));

    expect(apiFetch).not.toHaveBeenCalled();
  });

  it('isLoading is true before the first fetch resolves', () => {
    apiFetch.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useAdminAccounts());

    expect(result.current.isLoading).toBe(true);
  });

  it('create posts exactly {username, temporaryPassword}, no role field, then refetches (R35)', async () => {
    apiFetch.mockResolvedValue({ users: [] });
    const { result } = renderHook(() => useAdminAccounts());
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
    act(() => result.current.setNewUsername('nuevo'));
    act(() => result.current.setNewTemporaryPassword('temporal123'));

    await act(async () => result.current.create());

    expect(apiFetch).toHaveBeenCalledWith('/v1/users', {
      method: 'POST',
      body: { username: 'nuevo', temporaryPassword: 'temporal123' },
    });
    expect(apiFetch).toHaveBeenCalledTimes(3); // initial GET + POST + refetch GET
  });

  it('rename PATCHes {username} at the row id, then refetches', async () => {
    apiFetch.mockResolvedValue({ users: [account('u-1')] });
    const { result } = renderHook(() => useAdminAccounts());
    await waitFor(() => expect(result.current.accounts).toHaveLength(1));
    act(() => result.current.openRename(account('u-1')));
    act(() => result.current.setRenameDraft('nuevo-nombre'));

    await act(async () => result.current.saveRename());

    expect(apiFetch).toHaveBeenCalledWith('/v1/users/u-1', {
      method: 'PATCH',
      body: { username: 'nuevo-nombre' },
    });
    // Design.md section 9: every mutation refetches the list.
    expect(apiFetch).toHaveBeenCalledTimes(3); // initial GET + PATCH + refetch GET
    expect(apiFetch).toHaveBeenLastCalledWith('/v1/users');
  });

  it('reset routes through useConfirm before PATCHing {temporaryPassword} (R18)', async () => {
    apiFetch.mockResolvedValue({ users: [account('u-1')] });
    const { result } = renderHook(() => useAdminAccounts());
    await waitFor(() => expect(result.current.accounts).toHaveLength(1));
    act(() => result.current.openReset(account('u-1')));
    act(() => result.current.setResetDraft('otraTemporal1'));
    apiFetch.mockClear();

    act(() => result.current.saveReset());

    expect(result.current.confirm.pending).not.toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();

    await act(async () => result.current.confirm.confirm());

    expect(apiFetch).toHaveBeenCalledWith('/v1/users/u-1', {
      method: 'PATCH',
      body: { temporaryPassword: 'otraTemporal1' },
    });
  });

  it('remove routes through useConfirm before DELETEing the row id (R18)', async () => {
    apiFetch.mockResolvedValue({ users: [account('u-1')] });
    const { result } = renderHook(() => useAdminAccounts());
    await waitFor(() => expect(result.current.accounts).toHaveLength(1));
    apiFetch.mockClear();

    act(() => result.current.remove(account('u-1')));

    expect(result.current.confirm.pending).not.toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();

    await act(async () => result.current.confirm.confirm());

    expect(apiFetch).toHaveBeenCalledWith('/v1/users/u-1', { method: 'DELETE' });
    // Design.md section 9: every mutation refetches the list.
    expect(apiFetch).toHaveBeenCalledTimes(2); // DELETE + refetch GET
    expect(apiFetch).toHaveBeenLastCalledWith('/v1/users');
  });
});

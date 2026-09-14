// Admin account-management view state (T55, design.md section 5a). Plain
// apiFetch on mount, not usePolling - accounts is not one of FR-RT-01's four
// pollable resources. Every mutation refetches instead of tracking a marker.

import { useCallback, useEffect, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { useConfirm } from './useConfirm.js';
import { MESSAGES } from '../messages/index.js';

const USERS_URL = '/v1/users';

// R15 / design.md section 4.1: surface `error.detail` verbatim.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

export function useAdminAccounts({ active = true } = {}) {
  const [accounts, setAccounts] = useState(null); // null = loading
  const [error, setError] = useState(null);
  const confirm = useConfirm();

  const refetch = useCallback(async () => {
    try {
      const result = await apiFetch(USERS_URL);
      setAccounts(result.users);
      setError(null);
    } catch (err) {
      setError(toDetail(err));
    }
  }, []);

  // Inlined, not `refetch` - eslint's set-state-in-effect rule flags a named
  // async setState-caller invoked from an effect. See
  // progress/impl_frontend_spa.md -> "Auth screens, second half", deviation 7.
  useEffect(() => {
    if (!active) return undefined;
    let cancelled = false;
    apiFetch(USERS_URL).then(
      (result) => {
        if (!cancelled) {
          setAccounts(result.users);
          setError(null);
        }
      },
      (err) => {
        if (!cancelled) setError(toDetail(err));
      },
    );
    return () => {
      cancelled = true;
    };
  }, [active]);

  const [newUsername, setNewUsername] = useState('');
  const [newTemporaryPassword, setNewTemporaryPassword] = useState('');
  const canCreate = newUsername !== '' && newTemporaryPassword !== ''; // R35 - no role field

  const create = useCallback(async () => {
    if (!canCreate) return;
    try {
      await apiFetch(USERS_URL, {
        method: 'POST',
        body: { username: newUsername, temporaryPassword: newTemporaryPassword },
      });
      setNewUsername('');
      setNewTemporaryPassword('');
      setError(null);
      await refetch();
    } catch (err) {
      setError(toDetail(err));
    }
  }, [canCreate, newUsername, newTemporaryPassword, refetch]);

  // One row open for rename/reset at a time, same "single shared form" idiom
  // as useShoppingList.js's editingItem/draft.
  const [renamingId, setRenamingId] = useState(null);
  const [renameDraft, setRenameDraft] = useState('');
  const openRename = useCallback((account) => {
    setRenamingId(account.userId);
    setRenameDraft(account.username);
  }, []);
  const cancelRename = useCallback(() => setRenamingId(null), []);
  const canSaveRename = renameDraft !== '';
  const saveRename = useCallback(async () => {
    if (!canSaveRename) return;
    try {
      await apiFetch(`${USERS_URL}/${renamingId}`, {
        method: 'PATCH',
        body: { username: renameDraft },
      });
      setRenamingId(null);
      setError(null);
      await refetch();
    } catch (err) {
      setError(toDetail(err));
    }
  }, [canSaveRename, renamingId, renameDraft, refetch]);

  const [resettingId, setResettingId] = useState(null);
  const [resetDraft, setResetDraft] = useState('');
  const openReset = useCallback((account) => {
    setResettingId(account.userId);
    setResetDraft('');
  }, []);
  const cancelReset = useCallback(() => setResettingId(null), []);
  const canSaveReset = resetDraft !== '';
  const saveReset = useCallback(() => {
    if (!canSaveReset) return;
    const userId = resettingId;
    const temporaryPassword = resetDraft;
    confirm.requestConfirm(MESSAGES.ADMIN_ACCOUNTS_CONFIRM_RESET, async () => {
      // R18
      try {
        await apiFetch(`${USERS_URL}/${userId}`, { method: 'PATCH', body: { temporaryPassword } });
        setResettingId(null);
        setError(null);
        await refetch();
      } catch (err) {
        setError(toDetail(err));
      }
    });
  }, [canSaveReset, resettingId, resetDraft, confirm, refetch]);

  const remove = useCallback(
    (account) => {
      confirm.requestConfirm(MESSAGES.ADMIN_ACCOUNTS_CONFIRM_REMOVE, async () => {
        // R18
        try {
          await apiFetch(`${USERS_URL}/${account.userId}`, { method: 'DELETE' });
          setError(null);
          await refetch();
        } catch (err) {
          setError(toDetail(err));
        }
      });
    },
    [confirm, refetch],
  );

  return {
    accounts: accounts ?? [],
    isLoading: accounts === null,
    error,
    confirm,
    newUsername,
    setNewUsername,
    newTemporaryPassword,
    setNewTemporaryPassword,
    canCreate,
    create,
    renamingId,
    renameDraft,
    setRenameDraft,
    canSaveRename,
    openRename,
    saveRename,
    cancelRename,
    resettingId,
    resetDraft,
    setResetDraft,
    canSaveReset,
    openReset,
    saveReset,
    cancelReset,
    remove,
  };
}

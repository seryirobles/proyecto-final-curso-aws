// Shopping list view state (T35, design.md section 5): usePolling(GET
// /v1/shopping-list), add/edit/check/remove/resync. A 409
// SHOPPING_LIST_LOCK_HELD surfaces via `error` with no automatic retry -
// rest_api_contract.md section 3.3.

import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { usePolling } from './usePolling.js';
import { useConfirm } from './useConfirm.js';
import { parseMarker } from '../realtime/etag.js';
import { MESSAGES } from '../messages/index.js';

const SHOPPING_LIST_URL = '/v1/shopping-list';

function emptyDraft() {
  return { name: '', quantity: '', unit: '' };
}

// Pre-fills from the real item being edited (never a blank form) - the
// library slice's F4 data-loss bug, avoided by construction here.
function itemToDraft(item) {
  return { name: item.name, quantity: String(item.quantity), unit: item.unit };
}

// R15 / design.md section 4.1: surface `error.detail` verbatim, never a
// composed message.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

export function useShoppingList({ active = true } = {}) {
  const poll = usePolling(SHOPPING_LIST_URL, undefined, { enabled: active });
  const confirm = useConfirm();
  const [liveWeeks, setLiveWeeks] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [draft, setDraft] = useState(emptyDraft);
  const [isResyncing, setIsResyncing] = useState(false);
  const [error, setError] = useState(null);

  // One-time fetch, not a poll (design.md section 5's Screens table lists
  // only the shopping-list poll) - feeds the resync button's WeekLabel
  // scope (R21, FR-SHOP-05), same pattern as useWeekPlanner's live-weeks read.
  useEffect(() => {
    let cancelled = false;
    apiFetch('/v1/live-weeks').then(
      (result) => {
        if (!cancelled) setLiveWeeks(result);
      },
      () => {}, // scope label just stays hidden; the list itself doesn't depend on it
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const items = useMemo(() => poll.data?.items ?? [], [poll.data]);
  const uncheckedItems = useMemo(() => items.filter((item) => !item.checked), [items]);
  const checkedItems = useMemo(() => items.filter((item) => item.checked), [items]);

  const updateDraftField = useCallback(
    (field, value) => setDraft((current) => ({ ...current, [field]: value })),
    [],
  );

  const openAdd = useCallback(() => {
    setEditingItem(null);
    setDraft(emptyDraft());
    setIsFormOpen(true);
  }, []);
  const openEdit = useCallback((item) => {
    setEditingItem(item);
    setDraft(itemToDraft(item));
    setIsFormOpen(true);
  }, []);
  const closeForm = useCallback(() => setIsFormOpen(false), []);

  const canSaveItem = draft.name !== '' && draft.quantity !== '' && draft.unit !== '';

  const saveItem = useCallback(async () => {
    if (!canSaveItem) return;
    const path = editingItem
      ? `${SHOPPING_LIST_URL}/items/${editingItem.id}`
      : `${SHOPPING_LIST_URL}/items`;
    try {
      let marker = null;
      await apiFetch(path, {
        method: editingItem ? 'PUT' : 'POST',
        body: { name: draft.name, quantity: Number(draft.quantity), unit: draft.unit },
        onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
      });
      poll.applyMutationMarker(marker); // design.md section 4.2
      setError(null);
      setIsFormOpen(false);
      setEditingItem(null);
    } catch (err) {
      setError(toDetail(err));
    }
  }, [canSaveItem, editingItem, draft, poll]);

  const setChecked = useCallback(
    async (item, checked) => {
      try {
        let marker = null;
        await apiFetch(`${SHOPPING_LIST_URL}/items/${item.id}`, {
          method: 'PATCH',
          body: { checked },
          onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
        });
        poll.applyMutationMarker(marker);
        setError(null);
      } catch (err) {
        setError(toDetail(err));
      }
    },
    [poll],
  );

  const remove = useCallback(
    (itemId) => {
      confirm.requestConfirm(MESSAGES.CONFIRM_REMOVE_SHOPPING_ITEM, async () => {
        // R18
        try {
          let marker = null;
          await apiFetch(`${SHOPPING_LIST_URL}/items/${itemId}`, {
            method: 'DELETE',
            onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
          });
          poll.applyMutationMarker(marker);
          setError(null);
        } catch (err) {
          setError(toDetail(err));
        }
      });
    },
    [confirm, poll],
  );

  // No retry loop on a lock-held 409: a second press is by definition a
  // duplicate of the one already running (rest_api_contract.md section 3.3).
  const resync = useCallback(async () => {
    setIsResyncing(true);
    try {
      let marker = null;
      await apiFetch(`${SHOPPING_LIST_URL}/resync`, {
        method: 'POST',
        onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
      });
      poll.applyMutationMarker(marker);
      setError(null);
    } catch (err) {
      setError(toDetail(err));
    } finally {
      setIsResyncing(false);
    }
  }, [poll]);

  return {
    uncheckedItems,
    checkedItems,
    isLoading: poll.data === null, // R20
    connectionLost: poll.connectionLost,
    liveWeeks,
    isFormOpen,
    isEditing: editingItem != null,
    draft,
    updateDraftField,
    canSaveItem,
    openAdd,
    openEdit,
    closeForm,
    saveItem,
    setChecked,
    remove,
    confirm,
    isResyncing,
    resync,
    error, // R15 / design.md section 4.1
  };
}

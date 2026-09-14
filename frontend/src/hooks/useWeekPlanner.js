// Week planner state (T14, design.md section 4.2, section 5): live-weeks
// once, the selected week polled, and the definitive-slot mutations wired
// to usePolling's optimistic applyMutationMarker.

import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { usePolling } from './usePolling.js';
import { useConfirm } from './useConfirm.js';
import { useRecipeDetail, normalizeRecipeDetail } from './useRecipeDetail.js';
import { parseMarker } from '../realtime/etag.js';
import { MESSAGES } from '../messages/index.js';

const WEEK_DAYS = [1, 2, 3, 4, 5, 6, 7];
const WEEK_SLOTS = [1, 2];

function emptySlot(day, slot) {
  return { day, slot, candidates: [], definitiveId: null, isEmpty: true };
}

// Always 7 days x 2 slots (R1) regardless of which entries the API returned
// - the week read already fills every slot (routing.py `_get_week`), this
// is a defensive normalization, not a recompute of week boundaries.
export function buildWeekViewModel(payload) {
  if (!payload) return null;
  const bySlotKey = new Map(
    (payload.slots ?? []).map((entry) => [`${entry.day}-${entry.slot}`, entry]),
  );
  const days = WEEK_DAYS.map((day) => ({
    day,
    slots: WEEK_SLOTS.map((slot) => {
      const entry = bySlotKey.get(`${day}-${slot}`);
      if (!entry) return emptySlot(day, slot);
      return { ...entry, isEmpty: entry.candidates.length === 0 };
    }),
  }));
  return { weekId: payload.weekId, days };
}

function definitiveUrl(weekId, day, slot) {
  return `/v1/weeks/${weekId}/days/${day}/slots/${slot}/definitive`;
}

async function mutateDefinitive(url, options) {
  let marker = null;
  await apiFetch(url, {
    ...options,
    onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
  });
  return marker;
}

// R15 / design.md section 4.1: surface `error.detail` verbatim, never a
// composed message.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

export function useWeekPlanner({ active = true } = {}) {
  const [liveWeeks, setLiveWeeks] = useState(null);
  const [designation, setDesignation] = useState('current');
  const [authoringTarget, setAuthoringTarget] = useState(null);
  const [detailSource, setDetailSource] = useState(null);
  const [error, setError] = useState(null);
  const confirm = useConfirm();

  useEffect(() => {
    let cancelled = false;
    apiFetch('/v1/live-weeks').then(
      (result) => {
        if (!cancelled) setLiveWeeks(result);
      },
      (err) => {
        if (!cancelled) setError(toDetail(err));
      },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedWeek = liveWeeks?.[designation] ?? null;
  const weekUrl = selectedWeek ? `/v1/weeks/${selectedWeek.weekId}` : null;
  // `enabled` combines both gates (findings 1 and 2): only poll when this view
  // is on screen AND the URL is resolved - `usePolling(null)` would otherwise
  // fetch the literal string "null" before live-weeks resolves.
  const weekPoll = usePolling(weekUrl, undefined, { enabled: weekUrl !== null && active });
  const week = useMemo(() => buildWeekViewModel(weekPoll.data), [weekPoll.data]);
  const detail = useRecipeDetail(detailSource);

  const switchWeek = useCallback((nextDesignation) => setDesignation(nextDesignation), []);

  const openCandidateAuthoring = useCallback(
    (day, slot) => setAuthoringTarget({ weekId: selectedWeek?.weekId ?? null, day, slot }),
    [selectedWeek],
  );
  const closeCandidateAuthoring = useCallback(() => setAuthoringTarget(null), []);

  const openDetail = useCallback(
    (candidate) => setDetailSource({ recipe: normalizeRecipeDetail(candidate) }),
    [],
  );
  const closeDetail = useCallback(() => setDetailSource(null), []);

  const promoteDefinitive = useCallback(
    (day, slot, candidateId) => {
      const weekId = selectedWeek?.weekId;
      if (!weekId) return;
      const slotState = week?.days.find((d) => d.day === day)?.slots.find((s) => s.slot === slot);
      const doPromote = async () => {
        try {
          const marker = await mutateDefinitive(definitiveUrl(weekId, day, slot), {
            method: 'PUT',
            body: { candidateId },
          });
          weekPoll.applyMutationMarker(marker);
          setError(null);
        } catch (err) {
          setError(toDetail(err));
        }
      };
      if (slotState?.definitiveId && slotState.definitiveId !== candidateId) {
        confirm.requestConfirm(MESSAGES.CONFIRM_REPLACE_DEFINITIVE, doPromote); // R18
      } else {
        doPromote();
      }
    },
    [selectedWeek, week, weekPoll, confirm],
  );

  const clearDefinitive = useCallback(
    (day, slot) => {
      const weekId = selectedWeek?.weekId;
      if (!weekId) return;
      confirm.requestConfirm(MESSAGES.CONFIRM_CLEAR_DEFINITIVE, async () => {
        // R18
        try {
          const marker = await mutateDefinitive(definitiveUrl(weekId, day, slot), {
            method: 'DELETE',
          });
          weekPoll.applyMutationMarker(marker);
          setError(null);
        } catch (err) {
          setError(toDetail(err));
        }
      });
    },
    [selectedWeek, weekPoll, confirm],
  );

  return {
    liveWeeks,
    designation,
    week,
    isLoading: liveWeeks === null || week === null, // R20
    connectionLost: weekPoll.connectionLost,
    switchWeek,
    openCandidateAuthoring,
    authoringTarget,
    closeCandidateAuthoring,
    openDetail,
    detail: detail.recipe,
    isDetailLoading: detail.isLoading,
    detailError: detail.error,
    closeDetail,
    promoteDefinitive,
    clearDefinitive,
    confirm,
    error, // R15 / design.md section 4.1
  };
}

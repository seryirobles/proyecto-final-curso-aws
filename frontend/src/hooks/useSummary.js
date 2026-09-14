// Summary view state (T38-T40). See progress/impl_frontend_spa.md ->
// "Summary view (T38-T40)" for the polling/designation rationale.

import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { usePolling } from './usePolling.js';
import { useRecipeDetail, normalizeRecipeDetail } from './useRecipeDetail.js';
import { MESSAGES } from '../messages/index.js';

const WEEK_DAYS = [1, 2, 3, 4, 5, 6, 7];
const WEEK_SLOTS = [1, 2];

// R15 / design.md section 4.1: surface `error.detail` verbatim, never a
// composed message.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

// Backend's `summary()` (candidate.py) omits any slot with no definitive -
// regrouped here into the full 7x2 shape so the grid has a cell to skip
// (R19's whole-week EmptyState is `meals.length === 0`, not per-slot).
export function buildSummaryViewModel(payload) {
  if (!payload) return null;
  const bySlotKey = new Map(
    (payload.meals ?? []).map((entry) => [`${entry.day}-${entry.slot}`, entry.candidate]),
  );
  const days = WEEK_DAYS.map((day) => ({
    day,
    slots: WEEK_SLOTS.map((slot) => ({
      day,
      slot,
      candidate: bySlotKey.get(`${day}-${slot}`) ?? null,
    })),
  }));
  return { weekId: payload.weekId, days, isEmpty: (payload.meals ?? []).length === 0 };
}

export function useSummary({ active = true } = {}) {
  const [liveWeeks, setLiveWeeks] = useState(null);
  const [detailSource, setDetailSource] = useState(null);
  const [error, setError] = useState(null);

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

  const currentWeek = liveWeeks?.current ?? null;
  const summaryUrl = currentWeek ? `/v1/weeks/${currentWeek.weekId}/summary` : null;
  // Same double-gate as useWeekPlanner (findings 1 and 2).
  const summaryPoll = usePolling(summaryUrl, undefined, {
    enabled: summaryUrl !== null && active,
  });
  const summary = useMemo(() => buildSummaryViewModel(summaryPoll.data), [summaryPoll.data]);
  const detail = useRecipeDetail(detailSource);

  const openDetail = useCallback(
    (candidate) => setDetailSource({ recipe: normalizeRecipeDetail(candidate) }),
    [],
  );
  const closeDetail = useCallback(() => setDetailSource(null), []);

  return {
    week: currentWeek,
    summary,
    isLoading: liveWeeks === null || summary === null, // R20
    connectionLost: summaryPoll.connectionLost,
    openDetail,
    detail: detail.recipe,
    isDetailLoading: detail.isLoading,
    detailError: detail.error,
    closeDetail,
    error, // R15 / design.md section 4.1
  };
}

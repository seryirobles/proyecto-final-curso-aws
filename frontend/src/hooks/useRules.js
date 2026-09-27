// T32, design.md section 5. PUT /v1/rules/{ruleId} is a natural-key upsert
// (no edit-prefill flow, by design - see progress/impl_frontend_spa.md,
// "Rules view (T32-T34)"). Consumes FR-RULE-01...07; satisfiability is 6/27.

import { useCallback, useMemo, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { usePolling } from './usePolling.js';
import { useLibraryPicker } from './useLibraryPicker.js';
import { useConfirm } from './useConfirm.js';
import { parseMarker } from '../realtime/etag.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_LABELS, DAY_LABELS, SLOT_LABELS } from '../domain/labels.js';

const RULES_URL = '/v1/rules';

function computeRuleId(rule) {
  if (rule.type === 'categoryCount') return `cat#${rule.category}`;
  if (rule.type === 'pin') return `pin#${rule.day}#${rule.slot}`;
  return `day#${rule.day}`;
}

// Minimal es-ES descriptor, reused for the rule list and for a caught
// UNSATISFIABLE_RULE_SET's conflicts (R15) - `details.conflicts` is an array
// of the same encoded-rule shape GET /v1/rules returns (errors.py).
export function describeRule(rule) {
  if (rule.type === 'categoryCount') {
    return `${CATEGORY_LABELS[rule.category] ?? rule.category} × ${rule.count}`;
  }
  if (rule.type === 'pin') {
    return `${DAY_LABELS[rule.day]} · ${SLOT_LABELS[rule.slot]}`;
  }
  return DAY_LABELS[rule.day];
}

function emptyCategoryCountDraft() {
  return { category: '', count: '' };
}
function emptyPinDraft() {
  return { day: '', slot: '' };
}
function emptyDisabledDayDraft() {
  return { day: '' };
}

// R15 / design.md section 4.1: surface `error.detail` verbatim.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

// `UNSATISFIABLE_RULE_SET` needs its own handling - `details.conflicts` is a
// different shape than the plain detail string every other mutation
// surfaces (rest_api_contract.md's error table, errors.py `_unsatisfiable_details`).
function toRuleErrorDetail(err) {
  if (err instanceof ApiError && err.code === 'UNSATISFIABLE_RULE_SET') {
    const conflicts = err.details?.conflicts ?? [];
    if (conflicts.length > 0) {
      const list = conflicts.map(describeRule).join(', ');
      return `${err.detail} ${MESSAGES.RULES_CONFLICT_PREFIX} ${list}.`;
    }
  }
  return toDetail(err);
}

export function useRules({ active = true } = {}) {
  const poll = usePolling(RULES_URL, undefined, { enabled: active });
  const confirm = useConfirm();
  // R12 - RulesView's own instance (T32/T33); `active` gates both polls
  // (App shell fix round 1, finding 1).
  const picker = useLibraryPicker({ enabled: active });
  const [error, setError] = useState(null);

  const rules = useMemo(() => poll.data?.rules ?? [], [poll.data]);
  const categoryCounts = useMemo(() => rules.filter((r) => r.type === 'categoryCount'), [rules]);
  const pins = useMemo(() => rules.filter((r) => r.type === 'pin'), [rules]);
  const disabledDays = useMemo(() => rules.filter((r) => r.type === 'disabledDay'), [rules]);

  // R11: the three dropdown option sets come only from availableOptions, the
  // server's own pure-function output (rest_api_contract.md section 3.7) -
  // never re-derived from `rules` (architecture.md section 1.1).
  const availableOptions = poll.data?.availableOptions ?? null;
  const maxCountByCategory = useMemo(
    () => availableOptions?.maxCountByCategory ?? {},
    [availableOptions],
  );
  const daysAvailableForPin = useMemo(
    () => availableOptions?.daysAvailableForPin ?? [],
    [availableOptions],
  );
  const daysAvailableToDisable = useMemo(
    () => availableOptions?.daysAvailableToDisable ?? [],
    [availableOptions],
  );

  const pinDayOptions = useMemo(
    () => Object.entries(DAY_LABELS).filter(([day]) => daysAvailableForPin.includes(Number(day))),
    [daysAvailableForPin],
  );

  const disabledDayOptions = useMemo(
    () =>
      Object.entries(DAY_LABELS).filter(([day]) => daysAvailableToDisable.includes(Number(day))),
    [daysAvailableToDisable],
  );

  const putRule = useCallback(
    async (rule) => {
      try {
        let marker = null;
        await apiFetch(`${RULES_URL}/${encodeURIComponent(computeRuleId(rule))}`, {
          method: 'PUT',
          body: rule,
          onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
        });
        poll.applyMutationMarker(marker); // design.md section 4.2
        poll.refetchNow(); // issue ui-not-reflecting-mutations, E2
        setError(null);
        return true;
      } catch (err) {
        setError(toRuleErrorDetail(err));
        return false;
      }
    },
    [poll],
  );

  const remove = useCallback(
    (rule) => {
      confirm.requestConfirm(MESSAGES.CONFIRM_REMOVE_RULE, async () => {
        // R18
        try {
          let marker = null;
          await apiFetch(`${RULES_URL}/${encodeURIComponent(computeRuleId(rule))}`, {
            method: 'DELETE',
            onHeaders: (headers) => (marker = parseMarker(headers.get('ETag'))),
          });
          poll.applyMutationMarker(marker);
          poll.refetchNow(); // issue ui-not-reflecting-mutations, E3
          setError(null);
        } catch (err) {
          setError(toRuleErrorDetail(err));
        }
      });
    },
    [confirm, poll],
  );

  const [categoryCountDraft, setCategoryCountDraft] = useState(emptyCategoryCountDraft);
  const categoryCountOptions = useMemo(() => {
    if (categoryCountDraft.category === '') return [];
    const max = maxCountByCategory[categoryCountDraft.category] ?? 0;
    return Array.from({ length: max }, (_, i) => i + 1);
  }, [categoryCountDraft.category, maxCountByCategory]);
  // R8: an out-of-range count draft is cleared, not left dangling, when the
  // category change shrinks (or removes) its allowed range.
  const setCategoryCountCategory = useCallback(
    (category) =>
      setCategoryCountDraft((current) => {
        const max = maxCountByCategory[category] ?? 0;
        const stillValid = current.count !== '' && Number(current.count) <= max;
        return { category, count: stillValid ? current.count : '' };
      }),
    [maxCountByCategory],
  );
  const setCategoryCountCount = useCallback(
    (count) => setCategoryCountDraft((current) => ({ ...current, count })),
    [],
  );
  const canSaveCategoryCount =
    categoryCountDraft.category !== '' && categoryCountDraft.count !== '';
  const saveCategoryCount = useCallback(async () => {
    if (!canSaveCategoryCount) return;
    const ok = await putRule({
      type: 'categoryCount',
      category: categoryCountDraft.category,
      count: Number(categoryCountDraft.count),
    });
    if (ok) setCategoryCountDraft(emptyCategoryCountDraft());
  }, [canSaveCategoryCount, categoryCountDraft, putRule]);

  const [pinDraft, setPinDraft] = useState(emptyPinDraft);
  const [pinRecipeId, setPinRecipeId] = useState(null);
  const setPinDay = useCallback((day) => setPinDraft((current) => ({ ...current, day })), []);
  const setPinSlot = useCallback((slot) => setPinDraft((current) => ({ ...current, slot })), []);
  const canSavePin = pinDraft.day !== '' && pinDraft.slot !== '' && pinRecipeId != null;
  const savePin = useCallback(async () => {
    if (!canSavePin) return;
    const ok = await putRule({
      type: 'pin',
      day: Number(pinDraft.day),
      slot: Number(pinDraft.slot),
      recipeId: pinRecipeId,
    });
    if (ok) {
      setPinDraft(emptyPinDraft());
      setPinRecipeId(null);
    }
  }, [canSavePin, pinDraft, pinRecipeId, putRule]);

  const [disabledDayDraft, setDisabledDayDraft] = useState(emptyDisabledDayDraft);
  const setDisabledDayDay = useCallback((day) => setDisabledDayDraft({ day }), []);
  const canSaveDisabledDay = disabledDayDraft.day !== '';
  const saveDisabledDay = useCallback(async () => {
    if (!canSaveDisabledDay) return;
    const ok = await putRule({ type: 'disabledDay', day: Number(disabledDayDraft.day) });
    if (ok) setDisabledDayDraft(emptyDisabledDayDraft());
  }, [canSaveDisabledDay, disabledDayDraft, putRule]);

  return {
    categoryCounts,
    pins,
    disabledDays,
    isLoading: poll.data === null,
    connectionLost: poll.connectionLost,
    error,
    confirm,
    remove,
    picker,
    categoryCountDraft,
    categoryCountOptions,
    setCategoryCountCategory,
    setCategoryCountCount,
    canSaveCategoryCount,
    saveCategoryCount,
    pinDraft,
    pinDayOptions,
    setPinDay,
    setPinSlot,
    pinRecipeId,
    selectPinRecipe: setPinRecipeId,
    canSavePin,
    savePin,
    disabledDayDraft,
    disabledDayOptions,
    setDisabledDayDay,
    canSaveDisabledDay,
    saveDisabledDay,
  };
}

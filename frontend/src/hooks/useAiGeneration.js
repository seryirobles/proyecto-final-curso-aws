// Single-recipe AI generation (feature 28, rest_api_contract.md section 3.6):
// submit, poll the record on its own short interval, and hold the preview.
// No attempt field, no key hashing - the server derives both (R38).

import { useCallback, useEffect, useRef, useState } from 'react';
import { apiFetch, ApiError } from '../api/client.js';
import { MESSAGES } from '../messages/index.js';

export const AI_POLL_INTERVAL_MS = 2000;

const IN_FLIGHT = new Set(['pending', 'running']);
const IDLE = { phase: 'idle', generationId: null, recipe: null, failureMessage: null };

function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

function outcomeOf(generationId, response) {
  if (IN_FLIGHT.has(response.status)) return null;
  if (response.status === 'completed') {
    return { phase: 'completed', generationId, recipe: response.result, failureMessage: null };
  }
  const message = response.result?.error?.message ?? MESSAGES.GENERIC_ERROR;
  return { phase: 'failed', generationId, recipe: null, failureMessage: message };
}

export function useAiGeneration({ target, onAccept }) {
  const [state, setState] = useState(IDLE);
  const runRef = useRef(0);
  const timerRef = useRef(null);

  // Unmount ends any run: a bumped run id makes a late response inert (R41).
  useEffect(
    () => () => {
      runRef.current += 1;
      globalThis.clearTimeout(timerRef.current);
    },
    [],
  );

  const stop = useCallback(() => {
    runRef.current += 1;
    globalThis.clearTimeout(timerRef.current);
  }, []);

  const follow = useCallback(async (run, generationId) => {
    while (runRef.current === run) {
      await new Promise((resolve) => {
        timerRef.current = globalThis.setTimeout(resolve, AI_POLL_INTERVAL_MS);
      });
      if (runRef.current !== run) return;
      try {
        const response = await apiFetch(`/v1/generations/${generationId}`);
        if (runRef.current !== run) return;
        const outcome = outcomeOf(generationId, response);
        if (outcome) {
          setState(outcome);
          return;
        }
      } catch (err) {
        if (runRef.current !== run) return;
        setState({ ...IDLE, phase: 'failed', failureMessage: toDetail(err) });
        return;
      }
    }
  }, []);

  const generate = useCallback(
    async (source) => {
      if (!target) return;
      stop();
      const run = runRef.current;
      setState({ ...IDLE, phase: 'submitting' });
      try {
        const response = await apiFetch('/v1/generations', {
          method: 'POST',
          body: { type: 'recipe', target, source },
        });
        if (runRef.current !== run) return;
        const outcome = outcomeOf(response.generationId, response);
        if (outcome) {
          setState(outcome);
        } else {
          setState({ ...IDLE, phase: 'polling', generationId: response.generationId });
          follow(run, response.generationId);
        }
      } catch (err) {
        if (runRef.current !== run) return;
        setState({ ...IDLE, phase: 'failed', failureMessage: toDetail(err) });
      }
    },
    [target, stop, follow],
  );

  const discard = useCallback(async () => {
    const { generationId } = state;
    stop();
    setState(IDLE);
    if (!generationId) return;
    try {
      await apiFetch(`/v1/generations/${generationId}`, { method: 'DELETE' });
    } catch {
      // The preview is already cleared; an undeleted record only expires by TTL.
    }
  }, [state, stop]);

  const accept = useCallback(() => {
    if (state.phase !== 'completed') return;
    onAccept({ generationId: state.generationId, recipe: state.recipe });
  }, [state, onAccept]);

  return {
    phase: state.phase,
    isLoading: state.phase === 'submitting' || state.phase === 'polling',
    recipe: state.recipe,
    failureMessage: state.failureMessage,
    generate,
    discard,
    accept,
  };
}

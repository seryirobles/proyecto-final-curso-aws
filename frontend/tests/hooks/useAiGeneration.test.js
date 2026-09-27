// @vitest-environment jsdom
// Feature 28 (R33, R34, R36, R38, R39, R41): submit, poll, preview state.
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch, ApiError } from '../../src/api/client.js';
import { AI_POLL_INTERVAL_MS, useAiGeneration } from '../../src/hooks/useAiGeneration.js';

const TARGET = { kind: 'slot', weekId: '2026-W34', day: 3, slot: 1 };
const SOURCE = { kind: 'specification', ingredients: ['lentejas'], tools: ['olla'] };
const RECIPE = { name: 'Lentejas', category: 'legume', ingredients: [], tools: [], procedure: [] };

async function tick() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(AI_POLL_INTERVAL_MS);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  apiFetch.mockReset();
});
afterEach(() => vi.useRealTimers());

describe('useAiGeneration', () => {
  it('POSTs a recipe body with no attempt field and shows a loading state (R33, R38)', async () => {
    apiFetch.mockResolvedValueOnce({ generationId: 'g-1', status: 'pending' });
    const { result } = renderHook(() => useAiGeneration({ target: TARGET, onAccept: vi.fn() }));

    await act(async () => {
      await result.current.generate(SOURCE);
    });

    expect(apiFetch).toHaveBeenCalledWith('/v1/generations', {
      method: 'POST',
      body: { type: 'recipe', target: TARGET, source: SOURCE },
    });
    expect(Object.keys(apiFetch.mock.calls[0][1].body)).not.toContain('attempt');
    expect(result.current.isLoading).toBe(true);
  });

  it('polls until completed, then holds the previewed recipe (R33, R34)', async () => {
    apiFetch
      .mockResolvedValueOnce({ generationId: 'g-1', status: 'pending' })
      .mockResolvedValueOnce({ generationId: 'g-1', status: 'running', result: null })
      .mockResolvedValueOnce({ generationId: 'g-1', status: 'completed', result: RECIPE });
    const { result } = renderHook(() => useAiGeneration({ target: TARGET, onAccept: vi.fn() }));

    await act(async () => {
      await result.current.generate(SOURCE);
    });
    await tick();
    expect(result.current.isLoading).toBe(true);
    await tick();

    expect(apiFetch).toHaveBeenLastCalledWith('/v1/generations/g-1');
    expect(result.current.phase).toBe('completed');
    expect(result.current.recipe).toEqual(RECIPE);
    expect(result.current.isLoading).toBe(false);
  });

  it('shows the es-ES message from a failed record (R39)', async () => {
    apiFetch
      .mockResolvedValueOnce({ generationId: 'g-1', status: 'pending' })
      .mockResolvedValueOnce({
        generationId: 'g-1',
        status: 'failed',
        result: { error: { code: 'invalid_output', message: 'La receta no es válida.' } },
      });
    const { result } = renderHook(() => useAiGeneration({ target: TARGET, onAccept: vi.fn() }));

    await act(async () => {
      await result.current.generate(SOURCE);
    });
    await tick();

    expect(result.current.phase).toBe('failed');
    expect(result.current.failureMessage).toBe('La receta no es válida.');
  });

  it('shows the problem detail when the submit itself is rejected', async () => {
    apiFetch.mockRejectedValueOnce(
      new ApiError({ status: 422, code: 'MISSING_TOOLS', detail: 'Faltan utensilios.' }),
    );
    const { result } = renderHook(() => useAiGeneration({ target: TARGET, onAccept: vi.fn() }));

    await act(async () => {
      await result.current.generate(SOURCE);
    });

    expect(result.current.failureMessage).toBe('Faltan utensilios.');
  });

  it('an idempotent 200 that is already completed shows the preview without polling', async () => {
    apiFetch.mockResolvedValueOnce({ generationId: 'g-1', status: 'completed', result: RECIPE });
    const { result } = renderHook(() => useAiGeneration({ target: TARGET, onAccept: vi.fn() }));

    await act(async () => {
      await result.current.generate(SOURCE);
    });

    expect(result.current.phase).toBe('completed');
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });

  it('discard DELETEs the record and clears the preview (R36)', async () => {
    apiFetch.mockResolvedValueOnce({ generationId: 'g-1', status: 'completed', result: RECIPE });
    const { result } = renderHook(() => useAiGeneration({ target: TARGET, onAccept: vi.fn() }));
    await act(async () => {
      await result.current.generate(SOURCE);
    });
    apiFetch.mockResolvedValueOnce(null);

    await act(async () => {
      await result.current.discard();
    });

    expect(apiFetch).toHaveBeenLastCalledWith('/v1/generations/g-1', { method: 'DELETE' });
    expect(result.current.phase).toBe('idle');
    expect(result.current.recipe).toBeNull();
  });

  it('accept hands the generation id and recipe to onAccept (R35)', async () => {
    const onAccept = vi.fn();
    apiFetch.mockResolvedValueOnce({ generationId: 'g-1', status: 'completed', result: RECIPE });
    const { result } = renderHook(() => useAiGeneration({ target: TARGET, onAccept }));
    await act(async () => {
      await result.current.generate(SOURCE);
    });

    act(() => result.current.accept());

    expect(onAccept).toHaveBeenCalledWith({ generationId: 'g-1', recipe: RECIPE });
  });

  it('stops polling when it unmounts (R41)', async () => {
    apiFetch.mockResolvedValue({ generationId: 'g-1', status: 'pending' });
    const { result, unmount } = renderHook(() =>
      useAiGeneration({ target: TARGET, onAccept: vi.fn() }),
    );
    await act(async () => {
      await result.current.generate(SOURCE);
    });
    await tick();
    const callsBefore = apiFetch.mock.calls.length;

    unmount();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(AI_POLL_INTERVAL_MS * 5);
    });

    expect(apiFetch.mock.calls.length).toBe(callsBefore);
  });

  it('does nothing without a target', async () => {
    const { result } = renderHook(() => useAiGeneration({ target: null, onAccept: vi.fn() }));

    await act(async () => {
      await result.current.generate(SOURCE);
    });

    expect(apiFetch).not.toHaveBeenCalled();
  });
});

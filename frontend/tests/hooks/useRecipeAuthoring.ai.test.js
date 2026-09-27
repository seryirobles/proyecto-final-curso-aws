// @vitest-environment jsdom
// Feature 28 (R31, R32, R35, R37): the AI tab form-to-body mapping and accept routing.
import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/usePolling.js', () => ({
  usePolling: vi.fn(() => ({ data: null, connectionLost: false })),
}));
vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch } from '../../src/api/client.js';
import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';

const RECIPE = { name: 'Lentejas', category: 'legume', ingredients: [], tools: [], procedure: [] };
const SLOT = { weekId: '2026-W34', day: 3, slot: 1 };

beforeEach(() => apiFetch.mockReset());

function render(options = {}) {
  return renderHook(() =>
    useRecipeAuthoring({ mode: 'candidate', onSubmit: vi.fn(), aiTarget: SLOT, ...options }),
  );
}

describe('useRecipeAuthoring - ai method', () => {
  it('cannot generate until ingredients and tools are filled (R31)', () => {
    const { result } = render();
    expect(result.current.ai.canGenerate).toBe(false);

    act(() => result.current.updateAiSpec('ingredients', 'lentejas'));
    expect(result.current.ai.canGenerate).toBe(false);
    act(() => result.current.updateAiSpec('tools', 'olla'));
    expect(result.current.ai.canGenerate).toBe(true);
  });

  it('POSTs a specification body built from the form (R31)', async () => {
    apiFetch.mockResolvedValue({ generationId: 'g-1', status: 'pending' });
    const { result } = render();
    act(() => result.current.updateAiSpec('ingredients', 'lentejas, arroz\ncebolla'));
    act(() => result.current.updateAiSpec('tools', 'olla'));

    await act(async () => {
      await result.current.ai.generate();
    });

    expect(apiFetch).toHaveBeenCalledWith('/v1/generations', {
      method: 'POST',
      body: {
        type: 'recipe',
        target: { kind: 'slot', weekId: '2026-W34', day: 3, slot: 1 },
        source: {
          kind: 'specification',
          ingredients: ['lentejas', 'arroz', 'cebolla'],
          tools: ['olla'],
        },
      },
    });
  });

  it('POSTs a reference body once a library recipe is picked (R32)', async () => {
    apiFetch.mockResolvedValue({ generationId: 'g-1', status: 'pending' });
    const { result } = render({ mode: 'library', aiTarget: null });
    act(() => result.current.selectReferenceRecipe('r-1'));
    act(() => result.current.updateAiSpec('notes', 'sin gluten'));

    await act(async () => {
      await result.current.ai.generate();
    });

    expect(apiFetch.mock.calls[0][1].body).toEqual({
      type: 'recipe',
      target: { kind: 'library' },
      source: { kind: 'reference', recipeId: 'r-1', extraSpecifications: ['sin gluten'] },
    });
  });

  it('regenerate re-POSTs the form as it is now, adjusted or not (R37)', async () => {
    apiFetch.mockResolvedValue({ generationId: 'g-1', status: 'completed', result: RECIPE });
    const { result } = render();
    act(() => result.current.updateAiSpec('ingredients', 'lentejas'));
    act(() => result.current.updateAiSpec('tools', 'olla'));
    await act(async () => {
      await result.current.ai.generate();
    });

    act(() => result.current.updateAiSpec('ingredients', 'lentejas, chorizo'));
    await act(async () => {
      await result.current.ai.regenerate();
    });

    expect(apiFetch.mock.calls[1][1].body.source.ingredients).toEqual(['lentejas', 'chorizo']);
  });

  it('accepting in candidate mode submits the generation source (R35)', async () => {
    const onSubmit = vi.fn();
    apiFetch.mockResolvedValue({ generationId: 'g-1', status: 'completed', result: RECIPE });
    const { result } = render({ onSubmit });
    act(() => result.current.updateAiSpec('ingredients', 'lentejas'));
    act(() => result.current.updateAiSpec('tools', 'olla'));
    await act(async () => {
      await result.current.ai.generate();
    });

    act(() => result.current.ai.accept());

    expect(onSubmit).toHaveBeenCalledWith({ source: 'generation', generationId: 'g-1' });
  });

  it('accepting in library mode submits the previewed recipe as manual (R35)', async () => {
    const onSubmit = vi.fn();
    apiFetch.mockResolvedValue({ generationId: 'g-1', status: 'completed', result: RECIPE });
    const { result } = render({ mode: 'library', aiTarget: null, onSubmit });
    act(() => result.current.updateAiSpec('ingredients', 'lentejas'));
    act(() => result.current.updateAiSpec('tools', 'olla'));
    await act(async () => {
      await result.current.ai.generate();
    });

    act(() => result.current.ai.accept());

    expect(onSubmit).toHaveBeenCalledWith({ source: 'manual', recipe: RECIPE });
  });

  it('cannot generate for a slot whose week is unresolved', () => {
    const { result } = render({ aiTarget: { weekId: null, day: 1, slot: 1 } });
    act(() => result.current.updateAiSpec('ingredients', 'a'));
    act(() => result.current.updateAiSpec('tools', 'b'));

    expect(result.current.ai.canGenerate).toBe(false);
  });
});

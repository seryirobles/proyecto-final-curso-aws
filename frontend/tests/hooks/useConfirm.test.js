// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useConfirm } from '../../src/hooks/useConfirm.js';

describe('useConfirm', () => {
  it('requestConfirm sets pending with the message and handler', () => {
    const { result } = renderHook(() => useConfirm());
    const onConfirm = vi.fn();

    act(() => result.current.requestConfirm('¿Eliminar la receta?', onConfirm));

    expect(result.current.pending).toEqual({ message: '¿Eliminar la receta?', onConfirm });
  });

  it('confirm invokes the stored handler once and clears pending', () => {
    const { result } = renderHook(() => useConfirm());
    const onConfirm = vi.fn();
    act(() => result.current.requestConfirm('¿Eliminar la receta?', onConfirm));

    act(() => result.current.confirm());

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(result.current.pending).toBeNull();
  });

  it('cancel clears pending without invoking the handler', () => {
    const { result } = renderHook(() => useConfirm());
    const onConfirm = vi.fn();
    act(() => result.current.requestConfirm('¿Eliminar la receta?', onConfirm));

    act(() => result.current.cancel());

    expect(onConfirm).not.toHaveBeenCalled();
    expect(result.current.pending).toBeNull();
  });

  it('starts with no pending confirmation', () => {
    const { result } = renderHook(() => useConfirm());

    expect(result.current.pending).toBeNull();
  });
});

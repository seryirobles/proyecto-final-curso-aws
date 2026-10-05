// @vitest-environment jsdom
// R33, R34: scrollToDay scrolls the registered card and selects the day.

import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useDayStrip } from '../../src/hooks/useDayStrip.js';
import { DAY_SHORT_LABELS } from '../../src/domain/labels.js';

describe('DAY_SHORT_LABELS (R31)', () => {
  it('lists the three-letter names Monday to Sunday', () => {
    expect([1, 2, 3, 4, 5, 6, 7].map((d) => DAY_SHORT_LABELS[d])).toEqual([
      'Lun',
      'Mar',
      'Mié',
      'Jue',
      'Vie',
      'Sáb',
      'Dom',
    ]);
  });
});

describe('useDayStrip', () => {
  it('scrolls the registered node into view and selects the day', () => {
    const node = { scrollIntoView: vi.fn() };
    const { result } = renderHook(() => useDayStrip());
    expect(result.current.selectedDay).toBeNull();
    result.current.registerDay(3)(node);
    act(() => result.current.scrollToDay(3));
    expect(node.scrollIntoView).toHaveBeenCalledWith({ block: 'start', behavior: 'smooth' });
    expect(result.current.selectedDay).toBe(3);
  });

  it('selects a day whose card is not registered without throwing', () => {
    const { result } = renderHook(() => useDayStrip());
    act(() => result.current.scrollToDay(5));
    expect(result.current.selectedDay).toBe(5);
  });
});

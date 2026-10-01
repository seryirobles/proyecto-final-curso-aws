// @vitest-environment jsdom
// R10, R14: scroll once per open target; a rebuilt object with the same key is a no-op.
import { describe, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useScrollIntoView } from '../../src/hooks/useScrollIntoView.js';

function setup(initialKey) {
  const scrollIntoView = vi.fn();
  const ref = { current: { scrollIntoView } };
  const hook = renderHook(({ key }) => useScrollIntoView(ref, key), {
    initialProps: { key: initialKey },
  });
  return { scrollIntoView, hook };
}

describe('useScrollIntoView', () => {
  it('scrolls once on open with start/smooth (R10)', () => {
    const { scrollIntoView } = setup('a');

    expect(scrollIntoView).toHaveBeenCalledTimes(1);
    expect(scrollIntoView).toHaveBeenCalledWith({ block: 'start', behavior: 'smooth' });
  });

  it('does not scroll again when re-rendered with the same key (R14)', () => {
    const { scrollIntoView, hook } = setup('a');

    hook.rerender({ key: 'a' });
    hook.rerender({ key: 'a' });

    expect(scrollIntoView).toHaveBeenCalledTimes(1);
  });

  it('scrolls again when the key changes, and never for a null key (R10)', () => {
    const { scrollIntoView, hook } = setup(null);
    expect(scrollIntoView).not.toHaveBeenCalled();

    hook.rerender({ key: 'b' });
    hook.rerender({ key: 'c' });

    expect(scrollIntoView).toHaveBeenCalledTimes(2);
  });
});

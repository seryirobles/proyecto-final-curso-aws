// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen, cleanup } from '@testing-library/react';
import { LoadingState } from '../../src/components/LoadingState.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

describe('LoadingState', () => {
  it('renders the default loading message from MESSAGES', () => {
    render(<LoadingState />);

    expect(screen.queryByText(MESSAGES.LOADING_STATE_DEFAULT)).not.toBeNull();
  });

  it('renders a passed override message', () => {
    render(<LoadingState message="Generando receta…" />);

    expect(screen.queryByText('Generando receta…')).not.toBeNull();
  });

  it('renders a shimmer element whose tick state flips over time (T72)', () => {
    vi.useFakeTimers();
    render(<LoadingState />);
    const shimmer = screen.getByTestId('loading-shimmer');
    const before = shimmer.style.backgroundColor;

    act(() => {
      vi.advanceTimersByTime(600);
    });

    expect(shimmer.style.backgroundColor).not.toBe(before);
    vi.useRealTimers();
  });
});

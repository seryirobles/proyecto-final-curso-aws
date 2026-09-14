// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingState } from '../../src/components/LoadingState.jsx';
import { MESSAGES } from '../../src/messages/index.js';

describe('LoadingState', () => {
  it('renders the default loading message from MESSAGES', () => {
    render(<LoadingState />);

    expect(screen.queryByText(MESSAGES.LOADING_STATE_DEFAULT)).not.toBeNull();
  });

  it('renders a passed override message', () => {
    render(<LoadingState message="Generando receta…" />);

    expect(screen.queryByText('Generando receta…')).not.toBeNull();
  });
});

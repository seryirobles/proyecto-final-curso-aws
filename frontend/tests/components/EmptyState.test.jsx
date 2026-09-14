// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EmptyState } from '../../src/components/EmptyState.jsx';

describe('EmptyState', () => {
  it('renders the passed guidance message', () => {
    render(<EmptyState message="Todavía no hay recetas en la biblioteca." />);

    expect(screen.queryByText('Todavía no hay recetas en la biblioteca.')).not.toBeNull();
  });
});

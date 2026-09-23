// @vitest-environment jsdom
// Issue 11 (E4): the recipe detail keeps showing the estimated time once it is
// a bare minute count, next to a label that now names the unit (FR-MENU-04).
// Green before the fix as well as after - it guards the render path while the
// value's type changes under it.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { RecipeDetailView } from '../../src/components/RecipeDetailView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

function recipe(estimatedTime) {
  return {
    name: 'Lentejas al curry',
    category: 'legume',
    servings: 4,
    estimatedTime,
    ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
    tools: ['olla'],
    procedure: ['Sofreír la cebolla.'],
  };
}

describe('RecipeDetailView - estimated time in minutes', () => {
  it('renders the minute count next to its label (E4)', () => {
    render(<RecipeDetailView recipe={recipe(45)} onClose={vi.fn()} />);

    expect(screen.getByText(`${MESSAGES.RECIPE_DETAIL_ESTIMATED_TIME}: 45`)).not.toBeNull();
  });

  it('shows the label with no value when the recipe carries no time (E4)', () => {
    render(<RecipeDetailView recipe={recipe(null)} onClose={vi.fn()} />);

    expect(screen.getByText(`${MESSAGES.RECIPE_DETAIL_ESTIMATED_TIME}:`)).not.toBeNull();
  });
});

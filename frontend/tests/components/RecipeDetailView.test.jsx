// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { RecipeDetailView } from '../../src/components/RecipeDetailView.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { formatNumber } from '../../src/locale.js';

// `vite.config.js` sets `globals: false`, so @testing-library/react's
// auto-cleanup never registers - see WeekPlannerView.test.jsx.
afterEach(cleanup);

const RECIPE = {
  name: 'Lentejas al curry',
  category: 'legume',
  servings: 4,
  estimatedTime: '45 min',
  ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
  tools: ['olla'],
  procedure: ['Sofreír la cebolla.', 'Añadir las lentejas.'],
};

describe('RecipeDetailView', () => {
  it('renders nothing without a recipe', () => {
    const { container } = render(<RecipeDetailView recipe={null} onClose={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders ingredients with quantity/unit label, tools, procedure, time and servings (R4)', () => {
    render(<RecipeDetailView recipe={RECIPE} onClose={vi.fn()} />);

    expect(screen.getByText('Lentejas al curry')).not.toBeNull();
    expect(screen.getByText(`lentejas · ${formatNumber(300)} g`)).not.toBeNull();
    expect(screen.getByText('olla')).not.toBeNull();
    expect(screen.getByText('Sofreír la cebolla.')).not.toBeNull();
    expect(screen.getByText('Añadir las lentejas.')).not.toBeNull();
    expect(screen.getByText(`${MESSAGES.RECIPE_DETAIL_ESTIMATED_TIME}: 45 min`)).not.toBeNull();
    expect(
      screen.getByText(`${MESSAGES.RECIPE_DETAIL_SERVINGS}: ${formatNumber(4)}`),
    ).not.toBeNull();
  });

  it('renders the error detail when the fetch failed instead of nothing (R15)', () => {
    render(<RecipeDetailView recipe={null} error="No existe la receta." onClose={vi.fn()} />);

    expect(screen.getByText('No existe la receta.')).not.toBeNull();
  });

  it('calls onClose when the close control is clicked', () => {
    const onClose = vi.fn();
    render(<RecipeDetailView recipe={RECIPE} onClose={onClose} />);

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_DETAIL_CLOSE));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when the close control is clicked in the error branch (R15)', () => {
    const onClose = vi.fn();
    render(<RecipeDetailView recipe={null} error="No existe la receta." onClose={onClose} />);

    fireEvent.click(screen.getByText(MESSAGES.RECIPE_DETAIL_CLOSE));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

// @vitest-environment jsdom
// Feature 28 (R33, R34, R36, R37, R39, R40): the AI tab's loading, preview and failure states.
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { RecipeAuthoringForm } from '../../src/components/RecipeAuthoringForm.jsx';
import { MESSAGES } from '../../src/messages/index.js';

const RECIPE = {
  name: 'Lentejas estofadas',
  category: 'legume',
  ingredients: [{ name: 'lentejas', quantity: 300, unit: 'g' }],
  tools: ['olla'],
  procedure: ['Cocer las lentejas.'],
};

const PICKER = { recipes: [], filters: {}, setNameFilter: vi.fn(), setCategoryFilter: vi.fn() };

function props(ai) {
  return {
    mode: 'candidate',
    methods: ['library', 'scratch', 'ai'],
    method: 'ai',
    setMethod: vi.fn(),
    form: {},
    libraryPicker: PICKER,
    referencePicker: PICKER,
    selectReferenceRecipe: vi.fn(),
    referenceRecipeId: null,
    aiSpec: { ingredients: '', tools: '', notes: '' },
    updateAiSpec: vi.fn(),
    canSubmit: false,
    submit: vi.fn(),
    ai: {
      phase: 'idle',
      isLoading: false,
      canGenerate: true,
      generate: vi.fn(),
      regenerate: vi.fn(),
      accept: vi.fn(),
      discard: vi.fn(),
      ...ai,
    },
  };
}

afterEach(cleanup);

describe('RecipeAuthoringForm - ai tab', () => {
  it('shows a loading state while generating (R33)', () => {
    render(<RecipeAuthoringForm {...props({ phase: 'polling', isLoading: true })} />);

    expect(screen.getByText(MESSAGES.AI_GENERATING)).not.toBeNull();
  });

  it('the generate button calls ai.generate', () => {
    const p = props({});
    render(<RecipeAuthoringForm {...p} />);

    fireEvent.click(screen.getByText(MESSAGES.AI_GENERATE));

    expect(p.ai.generate).toHaveBeenCalled();
  });

  it('shows the preview with accept, regenerate and discard (R34, R36, R37)', () => {
    const p = props({ phase: 'completed', recipe: RECIPE });
    render(<RecipeAuthoringForm {...p} />);

    expect(screen.getByText('Lentejas estofadas')).not.toBeNull();
    fireEvent.click(screen.getByText(MESSAGES.AI_ACCEPT));
    fireEvent.click(screen.getByText(MESSAGES.AI_REGENERATE));
    fireEvent.click(screen.getByText(MESSAGES.AI_DISCARD));
    expect(p.ai.accept).toHaveBeenCalled();
    expect(p.ai.regenerate).toHaveBeenCalled();
    expect(p.ai.discard).toHaveBeenCalled();
  });

  it('shows the failure message (R39)', () => {
    const failed = { phase: 'failed', failureMessage: 'No se pudo generar.' };
    render(<RecipeAuthoringForm {...props(failed)} />);

    expect(screen.getByText('No se pudo generar.')).not.toBeNull();
  });

  it('renders no "not available yet" notice (R40)', () => {
    render(<RecipeAuthoringForm {...props({})} />);

    expect(screen.queryByText(/todavía no está disponible/)).toBeNull();
  });
});

// @vitest-environment jsdom
// F6 fix round 1: the shared filter markup LibraryRecipePicker/LibraryView
// both reuse instead of duplicating.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { LibraryFilters } from '../../src/components/LibraryFilters.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

describe('LibraryFilters', () => {
  it('renders the current name/category values and a full category list', () => {
    render(
      <LibraryFilters
        filters={{ name: 'lentejas', category: 'legume' }}
        setName={vi.fn()}
        setCategory={vi.fn()}
      />,
    );

    expect(screen.getByDisplayValue('lentejas')).not.toBeNull();
    expect(screen.getByText('Legumbres')).not.toBeNull();
  });

  it('typing in the name input calls setName', () => {
    const setName = vi.fn();
    render(
      <LibraryFilters
        filters={{ name: '', category: '' }}
        setName={setName}
        setCategory={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'tortilla' } });

    expect(setName).toHaveBeenCalledWith('tortilla');
  });

  it('changing the category select calls setCategory', () => {
    const setCategory = vi.fn();
    render(
      <LibraryFilters
        filters={{ name: '', category: '' }}
        setName={vi.fn()}
        setCategory={setCategory}
      />,
    );

    fireEvent.change(screen.getByText(MESSAGES.LIBRARY_PICKER_CATEGORY_ALL).closest('select'), {
      target: { value: 'legume' },
    });

    expect(setCategory).toHaveBeenCalledWith('legume');
  });
});

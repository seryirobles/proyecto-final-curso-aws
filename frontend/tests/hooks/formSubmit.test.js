// R25, R26: preventDefault always; the action runs only when submit is allowed.
import { describe, expect, it, vi } from 'vitest';
import { handleFormSubmit } from '../../src/hooks/formSubmit.js';

describe('handleFormSubmit', () => {
  it('prevents default and runs the action when allowed (R26)', () => {
    const event = { preventDefault: vi.fn() };
    const action = vi.fn();

    handleFormSubmit(event, true, action);

    expect(event.preventDefault).toHaveBeenCalledTimes(1);
    expect(action).toHaveBeenCalledTimes(1);
  });

  it('prevents default but ignores the submit when not allowed (R25)', () => {
    const event = { preventDefault: vi.fn() };
    const action = vi.fn();

    handleFormSubmit(event, false, action);

    expect(event.preventDefault).toHaveBeenCalledTimes(1);
    expect(action).not.toHaveBeenCalled();
  });
});

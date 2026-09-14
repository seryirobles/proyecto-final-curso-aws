// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConfirmDialog } from '../../src/components/ConfirmDialog.jsx';
import { MESSAGES } from '../../src/messages/index.js';

describe('ConfirmDialog', () => {
  it('renders nothing when there is no pending confirmation', () => {
    const { container } = render(
      <ConfirmDialog pending={null} onConfirm={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders the pending message and fires onConfirm/onCancel', () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        pending={{ message: '¿Eliminar la receta?', onConfirm: vi.fn() }}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );

    expect(screen.queryByText('¿Eliminar la receta?')).not.toBeNull();

    fireEvent.click(screen.getByText(MESSAGES.CONFIRM_DIALOG_CONFIRM));
    expect(onConfirm).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText(MESSAGES.CONFIRM_DIALOG_CANCEL));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});

// Pure component rendering `useConfirm`'s `pending` state (design.md section
// 4.4). No `window.confirm` - see design.md section 7 for the rejection.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

export function ConfirmDialog({ pending, onConfirm, onCancel }) {
  if (!pending) return null;

  return (
    <div
      data-testid="confirm-dialog-backdrop"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: tokens.color.backdrop,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          padding: tokens.space.lg,
          backgroundColor: tokens.color.surface,
          color: tokens.color.ink,
          borderRadius: tokens.radius.lg,
          boxShadow: tokens.shadow.lg,
        }}
      >
        <p style={{ margin: tokens.space.none, fontFamily: tokens.fontFamily.heading }}>
          {pending.message}
        </p>
        <div style={{ display: 'flex', gap: tokens.space.sm, marginTop: tokens.space.md }}>
          <button
            type="button"
            onClick={onCancel}
            style={{ padding: tokens.space.sm, borderRadius: tokens.radius.sm }}
          >
            {MESSAGES.CONFIRM_DIALOG_CANCEL}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            style={{
              padding: tokens.space.sm,
              backgroundColor: tokens.color.terra,
              color: tokens.color.surface,
              borderRadius: tokens.radius.sm,
            }}
          >
            {MESSAGES.CONFIRM_DIALOG_CONFIRM}
          </button>
        </div>
      </div>
    </div>
  );
}

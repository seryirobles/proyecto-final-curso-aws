// Pure component rendering `useConfirm`'s `pending` state (design.md section
// 4.4). No `window.confirm` - see design.md section 7 for the rejection.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

export function ConfirmDialog({ pending, onConfirm, onCancel }) {
  if (!pending) return null;

  return (
    <div
      style={{
        padding: tokens.space.lg,
        backgroundColor: tokens.color.surface,
        color: tokens.color.ink,
      }}
    >
      <p style={{ margin: tokens.space.none }}>{pending.message}</p>
      <div style={{ display: 'flex', gap: tokens.space.sm, marginTop: tokens.space.md }}>
        <button type="button" onClick={onCancel} style={{ padding: tokens.space.sm }}>
          {MESSAGES.CONFIRM_DIALOG_CANCEL}
        </button>
        <button
          type="button"
          onClick={onConfirm}
          style={{
            padding: tokens.space.sm,
            backgroundColor: tokens.color.terra,
            color: tokens.color.surface,
          }}
        >
          {MESSAGES.CONFIRM_DIALOG_CONFIRM}
        </button>
      </div>
    </div>
  );
}

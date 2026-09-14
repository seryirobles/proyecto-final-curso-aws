// One admin account row (T56, design.md section 5a): username/role/pending
// badge (R33); rename/reset/remove controls (R34); reset hidden on the
// acting admin's own row (R37); remove hidden on an admin-role row (R36).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { ROLE_LABELS } from '../domain/labels.js';

export function AccountRow({
  account,
  actingUserId,
  isRenaming,
  renameDraft,
  onRenameDraftChange,
  canSaveRename,
  onOpenRename,
  onSaveRename,
  onCancelRename,
  isResetting,
  resetDraft,
  onResetDraftChange,
  canSaveReset,
  onOpenReset,
  onSaveReset,
  onCancelReset,
  onRemove,
}) {
  // R37, fail-closed (fix round 1 finding 1): unknown actingUserId hides
  // reset on every row rather than showing it on every row.
  const isOwnRow = actingUserId == null || account.userId === actingUserId;
  const isAdminRow = account.role === 'Admin'; // R36

  return (
    <li style={{ padding: tokens.space.sm, display: 'flex', gap: tokens.space.sm }}>
      <span>{account.username}</span>
      <span>{ROLE_LABELS[account.role] ?? account.role}</span>
      {account.passwordResetRequired ? (
        <span style={{ color: tokens.color.ink2 }}>{MESSAGES.ADMIN_ACCOUNTS_PENDING_BADGE}</span>
      ) : null}

      {isRenaming ? (
        <>
          <input
            type="text"
            value={renameDraft}
            onChange={(e) => onRenameDraftChange(e.target.value)}
          />
          <button type="button" onClick={onSaveRename} disabled={!canSaveRename}>
            {MESSAGES.ADMIN_ACCOUNTS_RENAME}
          </button>
          <button type="button" onClick={onCancelRename}>
            {MESSAGES.ADMIN_ACCOUNTS_CANCEL}
          </button>
        </>
      ) : (
        <button type="button" onClick={onOpenRename}>
          {MESSAGES.ADMIN_ACCOUNTS_RENAME}
        </button>
      )}

      {!isOwnRow ? (
        isResetting ? (
          <>
            <input
              type="password"
              value={resetDraft}
              onChange={(e) => onResetDraftChange(e.target.value)}
            />
            <button type="button" onClick={onSaveReset} disabled={!canSaveReset}>
              {MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD}
            </button>
            <button type="button" onClick={onCancelReset}>
              {MESSAGES.ADMIN_ACCOUNTS_CANCEL}
            </button>
          </>
        ) : (
          <button type="button" onClick={onOpenReset}>
            {MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD}
          </button>
        )
      ) : null}

      {!isAdminRow ? (
        <button type="button" onClick={onRemove}>
          {MESSAGES.ADMIN_ACCOUNTS_REMOVE}
        </button>
      ) : null}
    </li>
  );
}

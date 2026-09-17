// The admin account-management screen (T56, design.md section 5a): create
// form (R35, no role selector) above a list of AccountRow (R33/R34/R36/R37).
// The only navigable view for an Admin (R30).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import {
  inputStyle,
  primaryButtonStyle,
  cardStyle,
  listResetStyle,
} from '../tokens/controlStyles.js';
import { EmptyState } from './EmptyState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { AccountRow } from './AccountRow.jsx';

export function AdminAccountsView({
  accounts,
  isLoading,
  error,
  actingUserId,
  newUsername,
  setNewUsername,
  newTemporaryPassword,
  setNewTemporaryPassword,
  canCreate,
  create,
  renamingId,
  renameDraft,
  setRenameDraft,
  canSaveRename,
  openRename,
  saveRename,
  cancelRename,
  resettingId,
  resetDraft,
  setResetDraft,
  canSaveReset,
  openReset,
  saveReset,
  cancelReset,
  remove,
  confirm,
}) {
  if (isLoading) return <LoadingState />;

  return (
    <div>
      <h2
        style={{
          margin: tokens.space.none,
          fontFamily: tokens.fontFamily.heading,
          fontSize: tokens.fontSize.xl,
        }}
      >
        {MESSAGES.ADMIN_ACCOUNTS_VIEW_TITLE}
      </h2>
      {error ? <p style={{ color: tokens.color.ink, padding: tokens.space.md }}>{error}</p> : null}

      <div
        style={{
          ...cardStyle,
          display: 'flex',
          gap: tokens.space.sm,
        }}
      >
        <label>
          {MESSAGES.ADMIN_ACCOUNTS_NEW_USERNAME_LABEL}
          <input
            type="text"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            style={inputStyle}
          />
        </label>
        <label>
          {MESSAGES.ADMIN_ACCOUNTS_TEMP_PASSWORD_LABEL}
          <input
            type="password"
            value={newTemporaryPassword}
            onChange={(e) => setNewTemporaryPassword(e.target.value)}
            style={inputStyle}
          />
        </label>
        <button
          type="button"
          onClick={create}
          disabled={!canCreate}
          style={primaryButtonStyle(!canCreate)}
        >
          {MESSAGES.ADMIN_ACCOUNTS_CREATE}
        </button>
      </div>

      {accounts.length === 0 ? (
        <EmptyState message={MESSAGES.ADMIN_ACCOUNTS_VIEW_EMPTY} />
      ) : (
        <ul
          style={{
            ...listResetStyle,
            margin: `${tokens.space.md} 0 0`,
            display: 'flex',
            flexDirection: 'column',
            gap: tokens.space.sm,
          }}
        >
          {accounts.map((account) => (
            <AccountRow
              key={account.userId}
              account={account}
              actingUserId={actingUserId}
              isRenaming={renamingId === account.userId}
              renameDraft={renameDraft}
              onRenameDraftChange={setRenameDraft}
              canSaveRename={canSaveRename}
              onOpenRename={() => openRename(account)}
              onSaveRename={saveRename}
              onCancelRename={cancelRename}
              isResetting={resettingId === account.userId}
              resetDraft={resetDraft}
              onResetDraftChange={setResetDraft}
              canSaveReset={canSaveReset}
              onOpenReset={() => openReset(account)}
              onSaveReset={saveReset}
              onCancelReset={cancelReset}
              onRemove={() => remove(account)}
            />
          ))}
        </ul>
      )}

      <ConfirmDialog
        pending={confirm.pending}
        onConfirm={confirm.confirm}
        onCancel={confirm.cancel}
      />
    </div>
  );
}

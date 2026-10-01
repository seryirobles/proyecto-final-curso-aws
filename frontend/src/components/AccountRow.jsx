// One admin account row (T56, design.md section 5a): username/role/pending
// badge (R33); rename/reset/remove controls (R34); reset hidden on the
// acting admin's own row (R37); remove hidden on an admin-role row (R36).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { ROLE_LABELS } from '../domain/labels.js';
import {
  inputStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  ghostButtonStyle,
  cardStyle,
} from '../tokens/controlStyles.js';
import { Banner } from './Banner.jsx';
import { handleFormSubmit } from '../hooks/formSubmit.js';

// T92 (design.md 10.6): avatar-circle (initials, no image dependency) plus
// role/status pill badges. Purely presentational - the R36/R37 gating below
// is untouched.
function initials(username) {
  return username.slice(0, 2).toUpperCase();
}

const rowFormStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  alignItems: 'center',
  gap: tokens.space.sm,
};

const badgeStyle = {
  display: 'inline-block',
  fontSize: tokens.fontSize.xs,
  fontWeight: 700,
  borderRadius: tokens.radius.pill,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
};

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
  error = null,
  isSavingRename = false,
  isSavingReset = false,
  isRemoving = false,
}) {
  // R37, fail-closed (fix round 1 finding 1): unknown actingUserId hides
  // reset on every row rather than showing it on every row.
  const isOwnRow = actingUserId == null || account.userId === actingUserId;
  const isAdminRow = account.role === 'Admin'; // R36

  return (
    <li
      style={{
        ...cardStyle,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: tokens.space.sm,
      }}
    >
      {isRenaming || isResetting ? (
        <div style={{ flexBasis: '100%' }}>
          <Banner>{error}</Banner>
        </div>
      ) : null}
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '2.25rem',
          height: '2.25rem',
          borderRadius: tokens.radius.pill,
          backgroundColor: isAdminRow ? tokens.color.terraSoft : tokens.color.oliveSoft,
          color: isAdminRow ? tokens.color.terra : tokens.color.olive,
          fontFamily: tokens.fontFamily.label,
          fontSize: tokens.fontSize.xs,
          fontWeight: 700,
          flex: 'none',
        }}
      >
        {initials(account.username)}
      </span>
      <span>{account.username}</span>
      <span
        style={{
          ...badgeStyle,
          color: isAdminRow ? tokens.color.terra : tokens.color.olive,
          backgroundColor: isAdminRow ? tokens.color.terraSoft : tokens.color.oliveSoft,
        }}
      >
        {ROLE_LABELS[account.role] ?? account.role}
      </span>
      {account.passwordResetRequired ? (
        <span
          style={{
            ...badgeStyle,
            color: tokens.color.honey,
            backgroundColor: tokens.color.honeySoft,
          }}
        >
          {MESSAGES.ADMIN_ACCOUNTS_PENDING_BADGE}
        </span>
      ) : null}

      {isRenaming ? (
        <form
          onSubmit={(e) => handleFormSubmit(e, canSaveRename, onSaveRename)}
          style={rowFormStyle}
        >
          <input
            type="text"
            name="username"
            autoComplete="off"
            spellCheck={false}
            autoCapitalize="none"
            value={renameDraft}
            onChange={(e) => onRenameDraftChange(e.target.value)}
            style={inputStyle}
          />
          <button
            type="submit"
            disabled={!canSaveRename || isSavingRename}
            style={primaryButtonStyle(!canSaveRename || isSavingRename)}
          >
            {MESSAGES.ADMIN_ACCOUNTS_RENAME}
          </button>
          <button type="button" onClick={onCancelRename} style={secondaryButtonStyle}>
            {MESSAGES.ADMIN_ACCOUNTS_CANCEL}
          </button>
        </form>
      ) : (
        <button type="button" onClick={onOpenRename} style={secondaryButtonStyle}>
          {MESSAGES.ADMIN_ACCOUNTS_RENAME}
        </button>
      )}

      {!isOwnRow ? (
        isResetting ? (
          <form
            onSubmit={(e) => handleFormSubmit(e, canSaveReset, onSaveReset)}
            style={rowFormStyle}
          >
            <input
              type="password"
              name="password"
              autoComplete="new-password"
              value={resetDraft}
              onChange={(e) => onResetDraftChange(e.target.value)}
              style={inputStyle}
            />
            <button
              type="submit"
              disabled={!canSaveReset || isSavingReset}
              style={primaryButtonStyle(!canSaveReset || isSavingReset)}
            >
              {MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD}
            </button>
            <button type="button" onClick={onCancelReset} style={secondaryButtonStyle}>
              {MESSAGES.ADMIN_ACCOUNTS_CANCEL}
            </button>
          </form>
        ) : (
          <button type="button" onClick={onOpenReset} style={secondaryButtonStyle}>
            {MESSAGES.ADMIN_ACCOUNTS_RESET_PASSWORD}
          </button>
        )
      ) : null}

      {!isAdminRow ? (
        <button type="button" onClick={onRemove} disabled={isRemoving} style={ghostButtonStyle}>
          {MESSAGES.ADMIN_ACCOUNTS_REMOVE}
        </button>
      ) : null}
    </li>
  );
}

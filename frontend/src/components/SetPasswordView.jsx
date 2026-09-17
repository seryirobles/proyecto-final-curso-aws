// The set-password screen (T52, design.md section 5a; card styling T80, section 10.6):
// renders only while a reset is pending (R26); new-password + confirm fields, a
// Cancelar control abandoning the attempt via session.logout (R28 - never a bypass).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

function pageStyle() {
  return {
    display: 'flex',
    justifyContent: 'center',
    minHeight: '100vh',
    padding: tokens.space.lg,
    backgroundColor: tokens.color.paper,
    fontFamily: tokens.fontFamily.body,
    color: tokens.color.ink,
  };
}

function cardStyle() {
  return {
    width: '100%',
    maxWidth: '420px',
    height: 'fit-content',
    backgroundColor: tokens.color.surface,
    border: `1px solid ${tokens.color.line}`,
    borderRadius: tokens.radius.md,
    boxShadow: tokens.shadow.md,
    padding: tokens.space.lg,
  };
}

// Same monogram idiom as LoginView.jsx (T79/T80 share one card treatment).
function badgeStyle() {
  return {
    width: '58px',
    height: '58px',
    margin: `${tokens.space.none} auto ${tokens.space.sm}`,
    borderRadius: tokens.radius.md,
    backgroundColor: tokens.color.terra,
    color: tokens.color.surface,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: tokens.fontFamily.heading,
    fontSize: tokens.fontSize.xxl,
  };
}

function titleStyle() {
  return {
    margin: tokens.space.none,
    fontFamily: tokens.fontFamily.heading,
    fontSize: tokens.fontSize.xl,
    color: tokens.color.ink,
    textAlign: 'center',
  };
}

function fieldLabelStyle() {
  return {
    display: 'block',
    fontFamily: tokens.fontFamily.label,
    fontSize: tokens.fontSize.xs,
    textTransform: 'uppercase',
    color: tokens.color.ink3,
    marginBottom: tokens.space.xs,
  };
}

function inputStyle() {
  return {
    width: '100%',
    border: `1px solid ${tokens.color.line2}`,
    backgroundColor: tokens.color.surface2,
    borderRadius: tokens.radius.sm,
    padding: tokens.space.sm,
    color: tokens.color.ink,
    fontFamily: tokens.fontFamily.body,
  };
}

function submitButtonStyle() {
  return {
    width: '100%',
    marginTop: tokens.space.md,
    border: 'none',
    borderRadius: tokens.radius.sm,
    backgroundColor: tokens.color.terra,
    color: tokens.color.surface,
    boxShadow: tokens.shadow.sm,
    padding: tokens.space.sm,
    fontFamily: tokens.fontFamily.body,
  };
}

// Ghost treatment (ConfirmDialog.jsx's cancel is the only other precedent -
// this one drops the border too, matching the prototype's plain text-link).
function cancelButtonStyle() {
  return {
    width: '100%',
    marginTop: tokens.space.sm,
    border: 'none',
    borderRadius: tokens.radius.sm,
    backgroundColor: 'transparent',
    color: tokens.color.ink3,
    padding: tokens.space.sm,
    fontFamily: tokens.fontFamily.body,
  };
}

// Warning idiom reused from ConnectionLostBanner.jsx (T74) - same
// honey/honeySoft palette, no new colour token introduced.
function mismatchStyle() {
  return {
    backgroundColor: tokens.color.honeySoft,
    color: tokens.color.ink,
    borderLeft: `4px solid ${tokens.color.honey}`,
    borderRadius: tokens.radius.sm,
    padding: tokens.space.sm,
    marginTop: tokens.space.sm,
  };
}

export function SetPasswordView({
  status,
  newPassword,
  setNewPassword,
  confirmPassword,
  setConfirmPassword,
  mismatch,
  canSubmit,
  submit,
  cancel,
  error,
  isSubmitting,
}) {
  if (status !== 'passwordResetPending') return null;

  return (
    <div style={pageStyle()}>
      <div style={cardStyle()}>
        <div style={badgeStyle()}>{MESSAGES.APP_TITLE.charAt(0)}</div>
        <h2 style={titleStyle()}>{MESSAGES.SET_PASSWORD_VIEW_TITLE}</h2>
        {error ? <p style={{ color: tokens.color.ink }}>{error}</p> : null}
        <label style={{ display: 'block', marginTop: tokens.space.md }}>
          <span style={fieldLabelStyle()}>{MESSAGES.SET_PASSWORD_NEW_LABEL}</span>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            style={inputStyle()}
          />
        </label>
        <label style={{ display: 'block', marginTop: tokens.space.sm }}>
          <span style={fieldLabelStyle()}>{MESSAGES.SET_PASSWORD_CONFIRM_LABEL}</span>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            style={inputStyle()}
          />
        </label>
        {mismatch ? <p style={mismatchStyle()}>{MESSAGES.SET_PASSWORD_MISMATCH}</p> : null}
        <button
          type="button"
          onClick={submit}
          disabled={!canSubmit || isSubmitting}
          style={submitButtonStyle()}
        >
          {MESSAGES.SET_PASSWORD_SUBMIT}
        </button>
        <button type="button" onClick={cancel} style={cancelButtonStyle()}>
          {MESSAGES.SET_PASSWORD_CANCEL}
        </button>
      </div>
    </div>
  );
}

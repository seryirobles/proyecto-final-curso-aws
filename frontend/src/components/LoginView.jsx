// The login screen (T50, design.md section 5a; card styling T79, section 10.6):
// username + password fields, a submit control, an inline error for a caught
// INVALID_CREDENTIALS. No registration control anywhere on this screen (R29).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { Banner } from './Banner.jsx';

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

// Monogram badge (design.md section 10.6, mined from the prototype's brand
// mark, Sobremesa.dc.html:70) - the letter comes from the app's own title
// key, never a second hardcoded brand string.
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
    boxSizing: 'border-box',
    border: `1px solid ${tokens.color.line2}`,
    backgroundColor: tokens.color.surface2,
    borderRadius: tokens.radius.sm,
    padding: tokens.space.sm,
    color: tokens.color.ink,
    fontSize: tokens.fontSize.input,
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

function footerNoteStyle() {
  return {
    textAlign: 'center',
    marginTop: tokens.space.md,
    paddingTop: tokens.space.sm,
    borderTop: `1px dashed ${tokens.color.line}`,
    fontFamily: tokens.fontFamily.label,
    fontSize: tokens.fontSize.xs,
    color: tokens.color.ink3,
  };
}

export function LoginView({
  username,
  setUsername,
  password,
  setPassword,
  canSubmit,
  submit,
  error,
  isSubmitting,
}) {
  return (
    <div style={pageStyle()}>
      <div style={cardStyle()}>
        <div style={badgeStyle()}>{MESSAGES.APP_TITLE.charAt(0)}</div>
        <h2 style={titleStyle()}>{MESSAGES.LOGIN_VIEW_TITLE}</h2>
        <label style={{ display: 'block', marginTop: tokens.space.md }}>
          <span style={fieldLabelStyle()}>{MESSAGES.LOGIN_USERNAME_LABEL}</span>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={inputStyle()}
          />
        </label>
        <label style={{ display: 'block', marginTop: tokens.space.sm }}>
          <span style={fieldLabelStyle()}>{MESSAGES.LOGIN_PASSWORD_LABEL}</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={inputStyle()}
          />
        </label>
        <Banner>{error}</Banner>
        <button
          type="button"
          onClick={submit}
          disabled={!canSubmit || isSubmitting}
          style={submitButtonStyle()}
        >
          {MESSAGES.LOGIN_SUBMIT}
        </button>
        <p style={footerNoteStyle()}>{MESSAGES.LOGIN_NO_REGISTRATION_NOTE}</p>
      </div>
    </div>
  );
}

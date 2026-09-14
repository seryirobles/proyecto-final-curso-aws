// The set-password screen (T52, design.md section 5a): renders only while a
// reset is pending (R26); new-password + confirm fields, a Cancelar control
// abandoning the attempt via session.logout (R28 - never a bypass).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

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
    <div style={{ padding: tokens.space.md }}>
      <h2 style={{ margin: tokens.space.none }}>{MESSAGES.SET_PASSWORD_VIEW_TITLE}</h2>
      {error ? <p style={{ color: tokens.color.ink }}>{error}</p> : null}
      <label>
        {MESSAGES.SET_PASSWORD_NEW_LABEL}
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
      </label>
      <label>
        {MESSAGES.SET_PASSWORD_CONFIRM_LABEL}
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
      </label>
      {mismatch ? (
        <p style={{ color: tokens.color.ink }}>{MESSAGES.SET_PASSWORD_MISMATCH}</p>
      ) : null}
      <div style={{ display: 'flex', gap: tokens.space.sm }}>
        <button type="button" onClick={submit} disabled={!canSubmit || isSubmitting}>
          {MESSAGES.SET_PASSWORD_SUBMIT}
        </button>
        <button type="button" onClick={cancel}>
          {MESSAGES.SET_PASSWORD_CANCEL}
        </button>
      </div>
    </div>
  );
}

// The login screen (T50, design.md section 5a): username + password fields,
// a submit control, an inline error for a caught INVALID_CREDENTIALS. No
// registration control anywhere on this screen (R29).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

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
    <div style={{ padding: tokens.space.md }}>
      <h2 style={{ margin: tokens.space.none }}>{MESSAGES.LOGIN_VIEW_TITLE}</h2>
      {error ? <p style={{ color: tokens.color.ink }}>{error}</p> : null}
      <label>
        {MESSAGES.LOGIN_USERNAME_LABEL}
        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
      </label>
      <label>
        {MESSAGES.LOGIN_PASSWORD_LABEL}
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </label>
      <button type="button" onClick={submit} disabled={!canSubmit || isSubmitting}>
        {MESSAGES.LOGIN_SUBMIT}
      </button>
    </div>
  );
}

// Login screen state (T50, design.md section 5a): username/password draft
// fields, submit -> session.login, inline INVALID_CREDENTIALS error (R24,
// R25). No registration control anywhere on this screen (R29).

import { useCallback, useState } from 'react';
import { ApiError } from '../api/client.js';
import { MESSAGES } from '../messages/index.js';

// R15 / design.md section 4.1: surface `error.detail` verbatim, never a
// composed message.
function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

export function useLoginForm(session) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit = username !== '' && password !== '';

  const submit = useCallback(async () => {
    if (!canSubmit) return;
    setIsSubmitting(true);
    try {
      await session.login(username, password);
      setError(null);
    } catch (err) {
      setError(toDetail(err));
    } finally {
      setIsSubmitting(false);
    }
  }, [canSubmit, session, username, password]);

  return { username, setUsername, password, setPassword, canSubmit, submit, error, isSubmitting };
}

// Set-password screen state (T52, design.md section 5a): new-password +
// confirm fields checked client-side for an exact match, submit ->
// session.setPassword, cancel -> session.logout (R26, R27). Length/
// composition policy is FR-AUTH-15, enforced server-side.

import { useCallback, useState } from 'react';
import { ApiError } from '../api/client.js';
import { MESSAGES } from '../messages/index.js';

function toDetail(err) {
  return err instanceof ApiError ? err.detail : MESSAGES.GENERIC_ERROR;
}

export function useSetPasswordForm(session) {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const mismatch = confirmPassword !== '' && newPassword !== confirmPassword;
  const canSubmit = newPassword !== '' && confirmPassword !== '' && !mismatch;

  const submit = useCallback(async () => {
    if (!canSubmit) return; // R27 - a mismatched confirm field blocks submit
    setIsSubmitting(true);
    try {
      await session.setPassword(newPassword);
      setError(null);
    } catch (err) {
      setError(toDetail(err));
    } finally {
      setIsSubmitting(false);
    }
  }, [canSubmit, session, newPassword]);

  const cancel = useCallback(() => session.logout(), [session]);

  return {
    status: session.session.status,
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
  };
}

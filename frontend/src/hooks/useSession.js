// Session-status state machine (design.md section 5a): GET /v1/live-weeks
// mount probe maps 200/FORBIDDEN/PASSWORD_RESET_PENDING onto the four states.
// See progress/impl_frontend_spa.md -> "Auth screens, second half", finding 1.

import { useCallback, useEffect, useState } from 'react';
import { apiFetch } from '../api/client.js';
import { roleFromWire } from '../domain/wireCodes.js';

const LIVE_WEEKS_URL = '/v1/live-weeks';

// Known limitation: an Admin with a pending reset probes as FORBIDDEN, not
// PASSWORD_RESET_PENDING (backend checks role first). See
// progress/impl_frontend_spa.md "Auth screens, first half".
function classifyProbeFailure(err) {
  if (err.code === 'PASSWORD_RESET_PENDING') return { status: 'passwordResetPending' };
  if (err.code === 'FORBIDDEN') return { status: 'authenticated', role: 'Admin' };
  return { status: 'anonymous' }; // SESSION_EXPIRED, or no cookie at all
}

export function useSession() {
  const [session, setSession] = useState({ status: 'loading' });

  const probe = useCallback(
    () =>
      apiFetch(LIVE_WEEKS_URL).then(
        () => setSession({ status: 'authenticated', role: 'User' }),
        (err) => setSession(classifyProbeFailure(err)),
      ),
    [],
  );

  useEffect(() => {
    probe();
  }, [probe]); // R23 - the mount-time check

  // Errors are left to propagate - the calling view hook (useLoginForm,
  // useSetPasswordForm) owns its own inline error state, same convention
  // every other mutation-issuing hook already follows (client.js).
  const login = useCallback(async (username, password) => {
    const result = await apiFetch('/v1/session', {
      method: 'POST',
      body: { username, password },
    }); // R25
    setSession(
      result.passwordResetRequired
        ? { status: 'passwordResetPending' }
        : { status: 'authenticated', role: roleFromWire(result.role), userId: result.userId },
    );
  }, []);

  const setPassword = useCallback(
    async (newPassword) => {
      await apiFetch('/v1/session/password', { method: 'PUT', body: { newPassword } }); // R27
      await probe(); // role wasn't known at login time; re-run the mount check
    },
    [probe],
  );

  const logout = useCallback(async () => {
    await apiFetch('/v1/session', { method: 'DELETE' });
    setSession({ status: 'anonymous' });
  }, []); // R32

  return { session, login, setPassword, logout };
}

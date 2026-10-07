// Active-view state, no router library (design.md section 5); `navTargets` is role-gated
// (R30, R31; progress/impl_frontend_spa.md). Mirrors the URL hash for a User (frontend_ux_phase2 R45-R52).

import { useCallback, useEffect, useState } from 'react';
import { useSession } from './useSession.js';
import { hashToView, viewToHash } from './viewHash.js';

export const VIEWS = ['summary', 'week', 'library', 'rules', 'shoppingList'];

const DEFAULT_VIEW = 'summary'; // landing view (R58, R59)

export function useApp() {
  const [activeView, setActiveView] = useState(
    () => hashToView(window.location.hash) ?? DEFAULT_VIEW,
  );
  const { session, login, setPassword, logout } = useSession();

  const isAuthenticatedUser = session.status === 'authenticated' && session.role === 'User';
  const navTargets = isAuthenticatedUser ? VIEWS : [];

  // Unknown or empty hash: default view, hash replaced (R58).
  const syncFromHash = useCallback(() => {
    const view = hashToView(window.location.hash);
    setActiveView(view ?? DEFAULT_VIEW);
    if (view === null) window.history.replaceState(null, '', viewToHash(DEFAULT_VIEW));
  }, []);

  useEffect(() => {
    if (!isAuthenticatedUser) return undefined;
    if (hashToView(window.location.hash) === null) {
      window.history.replaceState(null, '', viewToHash(DEFAULT_VIEW)); // R58
    }
    window.addEventListener('popstate', syncFromHash);
    return () => window.removeEventListener('popstate', syncFromHash);
  }, [isAuthenticatedUser, syncFromHash]); // R49, R58

  const navigateTo = (view) => {
    if (isAuthenticatedUser && view !== activeView) {
      window.history.pushState(null, '', viewToHash(view)); // R46, R47
    }
    setActiveView(view);
  };

  const logoutAndClearHash = async () => {
    await logout();
    setActiveView(DEFAULT_VIEW); // a later login starts on summary (R59)
    if (isAuthenticatedUser) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search); // R52
    }
  };

  return {
    activeView,
    navigateTo,
    session,
    login,
    setPassword,
    logout: logoutAndClearHash,
    navTargets,
  };
}

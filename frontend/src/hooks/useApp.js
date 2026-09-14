// Owns the SPA's one active-view state value (design.md section 5) - no
// router library. Exposes `navTargets`, the role-gated subset of VIEWS
// (R30, R31); see progress/impl_frontend_spa.md "Auth screens, first half".

import { useState } from 'react';
import { useSession } from './useSession.js';

export const VIEWS = ['week', 'library', 'rules', 'shoppingList', 'summary'];

export function useApp() {
  const [activeView, setActiveView] = useState('week');
  const { session, login, setPassword, logout } = useSession();

  const isAuthenticatedUser = session.status === 'authenticated' && session.role === 'User';
  const navTargets = isAuthenticatedUser ? VIEWS : [];

  return {
    activeView,
    navigateTo: (view) => setActiveView(view),
    session,
    login,
    setPassword,
    logout,
    navTargets,
  };
}

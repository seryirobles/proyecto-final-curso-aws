// The app shell (T42/T58-T59; design.md section 5, 5a): 4-way session-status
// render branch (R23/R30/R31) gates which shell mounts, then per-view active
// gating. See progress/impl_frontend_spa.md -> "App shell"/"Auth screens".

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { useApp } from '../hooks/useApp.js';
import { useLoginForm } from '../hooks/useLoginForm.js';
import { useSetPasswordForm } from '../hooks/useSetPasswordForm.js';
import { useAdminAccounts } from '../hooks/useAdminAccounts.js';
import { useWeekPlanner } from '../hooks/useWeekPlanner.js';
import { useLibrary } from '../hooks/useLibrary.js';
import { useRules } from '../hooks/useRules.js';
import { useShoppingList } from '../hooks/useShoppingList.js';
import { useSummary } from '../hooks/useSummary.js';
import { LoginView } from './LoginView.jsx';
import { SetPasswordView } from './SetPasswordView.jsx';
import { AdminAccountsView } from './AdminAccountsView.jsx';
import { WeekPlannerView } from './WeekPlannerView.jsx';
import { LibraryView } from './LibraryView.jsx';
import { RulesView } from './RulesView.jsx';
import { ShoppingListView } from './ShoppingListView.jsx';
import { SummaryView } from './SummaryView.jsx';
import { ConnectionLostBanner } from './ConnectionLostBanner.jsx';
import { LoadingState } from './LoadingState.jsx';

// Labels keyed by useApp.js's VIEWS, not a second hardcoded view list (finding 5a).
const NAV_LABELS = {
  week: MESSAGES.NAV_WEEK,
  library: MESSAGES.NAV_LIBRARY,
  rules: MESSAGES.NAV_RULES,
  shoppingList: MESSAGES.NAV_SHOPPING_LIST,
  summary: MESSAGES.NAV_SUMMARY,
};

// T71 (design.md section 10.5): the app-wide type/colour foundation - every
// descendant inherits fontFamily/color through normal CSS inheritance.
function rootShellStyle() {
  return {
    fontFamily: tokens.fontFamily.body,
    background: tokens.color.paper,
    color: tokens.color.ink,
    minHeight: '100vh',
  };
}

function navButtonStyle(isActive) {
  return {
    padding: tokens.space.sm,
    borderRadius: tokens.radius.pill,
    backgroundColor: isActive ? tokens.color.terraSoft : tokens.color.surface,
    border: `1px solid ${tokens.color.line}`,
  };
}

function logoutButtonStyle() {
  return {
    padding: tokens.space.sm,
    borderRadius: tokens.radius.pill,
    backgroundColor: tokens.color.surface,
    border: `1px solid ${tokens.color.line}`,
  };
}

function headerStyle() {
  return {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: tokens.space.md,
    backgroundColor: tokens.color.surface,
    borderBottom: `1px solid ${tokens.color.line}`,
    boxShadow: tokens.shadow.sm,
  };
}

export function App() {
  const { activeView, navigateTo, session, login, setPassword, logout, navTargets } = useApp();
  // useLoginForm/useSetPasswordForm expect the whole useSession()-shaped
  // object (session + its 3 actions), matching their own signatures.
  const sessionApi = { session, login, setPassword, logout };
  const loginForm = useLoginForm(sessionApi);
  const setPasswordForm = useSetPasswordForm(sessionApi);

  const isAdmin = session.status === 'authenticated' && session.role === 'Admin';
  const isUser = session.status === 'authenticated' && session.role === 'User';

  // Every hook still runs every render (Rules of Hooks); `active` keeps each
  // one's polling/fetch off until its shell and view are both the live one.
  const weekPlanner = useWeekPlanner({ active: isUser && activeView === 'week' });
  const library = useLibrary({ active: isUser && activeView === 'library' });
  const rules = useRules({ active: isUser && activeView === 'rules' });
  const shoppingList = useShoppingList({ active: isUser && activeView === 'shoppingList' });
  const summary = useSummary({ active: isUser && activeView === 'summary' });
  const adminAccounts = useAdminAccounts({ active: isAdmin });

  // R23/R30/R31 - the 4-way render branch. No case falls through to another:
  // each of `loading`/`anonymous`/`passwordResetPending` returns on its own,
  // and Admin/User are separate, mutually exclusive shells below.
  if (session.status === 'loading') return <LoadingState />;
  if (session.status === 'anonymous') return <LoginView {...loginForm} />;
  if (session.status === 'passwordResetPending') return <SetPasswordView {...setPasswordForm} />;

  if (isAdmin) {
    return (
      <div style={rootShellStyle()}>
        <div style={headerStyle()}>
          <h1 style={{ margin: tokens.space.none, color: tokens.color.ink }}>
            {MESSAGES.APP_TITLE}
          </h1>
          <button type="button" onClick={logout} style={logoutButtonStyle()}>
            {MESSAGES.APP_LOGOUT}
          </button>
        </div>
        <main style={{ padding: tokens.space.md }}>
          <AdminAccountsView {...adminAccounts} actingUserId={session.userId} />
        </main>
      </div>
    );
  }

  if (isUser) {
    const navItems = navTargets.map((view) => ({ view, label: NAV_LABELS[view] }));
    const activeConnectionLost = {
      week: weekPlanner,
      library,
      rules,
      shoppingList,
      summary,
    }[activeView].connectionLost;

    return (
      <div style={rootShellStyle()}>
        <div style={headerStyle()}>
          <h1 style={{ margin: tokens.space.none, color: tokens.color.ink }}>
            {MESSAGES.APP_TITLE}
          </h1>
          <button type="button" onClick={logout} style={logoutButtonStyle()}>
            {MESSAGES.APP_LOGOUT}
          </button>
        </div>
        <nav style={{ display: 'flex', gap: tokens.space.sm, padding: tokens.space.md }}>
          {navItems.map((item) => (
            <button
              key={item.view}
              type="button"
              onClick={() => navigateTo(item.view)}
              style={navButtonStyle(activeView === item.view)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <ConnectionLostBanner connectionLost={activeConnectionLost} />
        <main style={{ padding: tokens.space.md }}>
          {activeView === 'week' ? <WeekPlannerView {...weekPlanner} /> : null}
          {activeView === 'library' ? <LibraryView {...library} /> : null}
          {activeView === 'rules' ? <RulesView {...rules} /> : null}
          {activeView === 'shoppingList' ? <ShoppingListView {...shoppingList} /> : null}
          {activeView === 'summary' ? <SummaryView {...summary} /> : null}
        </main>
      </div>
    );
  }

  return null; // Unreachable: authenticated always carries a User or Admin role.
}

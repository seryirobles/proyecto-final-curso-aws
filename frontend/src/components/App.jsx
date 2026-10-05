// The app shell (T42/T58-T59; design.md section 5, 5a): 4-way session-status
// render branch (R23/R30/R31) gates which shell mounts, then per-view active
// gating. See progress/impl_frontend_spa.md -> "App shell"/"Auth screens".

import { tokens } from '../tokens/index.js';
import { targetStyle } from '../tokens/controlStyles.js';
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
import { useViewport, VIEWPORT } from '../hooks/useViewport.js';
import { useDocumentTitle } from '../hooks/useDocumentTitle.js';
import { useScrollToTop } from '../hooks/useScrollToTop.js';
import { NavIcon } from './NavIcons.jsx';
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

// Short labels for the tab bar, where five buttons share 375 px (R10).
const TAB_LABELS = { ...NAV_LABELS, shoppingList: MESSAGES.NAV_SHOPPING_LIST_SHORT };

// calc() needs a length operand: unitless 0 is invalid there (R12); jsdom also drops bare env().
const SAFE_AREA_BOTTOM = 'calc(0px + env(safe-area-inset-bottom))';

// Active = bold + terra border besides the fill (R14, WCAG 1.4.11).
function activeMarkStyle(isActive) {
  return {
    fontWeight: isActive ? 700 : 400,
    border: `1px solid ${isActive ? tokens.color.terra : tokens.color.line}`,
  };
}

function navButtonStyle(isActive) {
  return {
    padding: tokens.space.sm,
    borderRadius: tokens.radius.pill,
    backgroundColor: isActive ? tokens.color.terraSoft : tokens.color.surface,
    ...activeMarkStyle(isActive),
  };
}

function tabBarStyle() {
  return {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    display: 'flex',
    backgroundColor: tokens.color.surface,
    borderTop: `1px solid ${tokens.color.line}`,
    paddingBottom: SAFE_AREA_BOTTOM,
  };
}

function tabButtonStyle(isActive) {
  return {
    flex: 1,
    minHeight: tokens.layout.tabBarHeight,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: tokens.space.xs,
    padding: tokens.space.xs,
    fontSize: tokens.fontSize.xs,
    color: tokens.color.ink,
    backgroundColor: isActive ? tokens.color.terraSoft : tokens.color.surface,
    ...activeMarkStyle(isActive),
  };
}

function mainStyle(isCompact, hasTabBar) {
  return {
    padding: tokens.space.md,
    maxWidth: tokens.layout.contentMax,
    margin: '0 auto',
    ...(isCompact && hasTabBar
      ? { paddingBottom: `calc(${tokens.layout.tabBarHeight} + env(safe-area-inset-bottom))` }
      : null),
  };
}

function logoutButtonStyle(viewport) {
  return {
    ...targetStyle(viewport),
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
    position: 'sticky',
    top: 0,
    minHeight: tokens.layout.headerHeight,
    boxSizing: 'border-box',
  };
}

export function App() {
  const { activeView, navigateTo, session, login, setPassword, logout, navTargets } = useApp();
  const viewport = useViewport();
  const isCompact = viewport === VIEWPORT.COMPACT;
  // useLoginForm/useSetPasswordForm expect the whole useSession()-shaped
  // object (session + its 3 actions), matching their own signatures.
  const sessionApi = { session, login, setPassword, logout };
  const loginForm = useLoginForm(sessionApi);
  const setPasswordForm = useSetPasswordForm(sessionApi);

  const isAdmin = session.status === 'authenticated' && session.role === 'Admin';
  const isUser = session.status === 'authenticated' && session.role === 'User';
  useDocumentTitle(isUser ? NAV_LABELS[activeView] : null);
  useScrollToTop(activeView);

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
          <button type="button" onClick={logout} style={logoutButtonStyle(viewport)}>
            {MESSAGES.APP_LOGOUT}
          </button>
        </div>
        <main style={mainStyle(isCompact, false)}>
          <AdminAccountsView {...adminAccounts} actingUserId={session.userId} viewport={viewport} />
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
          <button type="button" onClick={logout} style={logoutButtonStyle(viewport)}>
            {MESSAGES.APP_LOGOUT}
          </button>
        </div>
        <nav
          style={
            isCompact
              ? tabBarStyle()
              : {
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: tokens.space.sm,
                  padding: tokens.space.md,
                }
          }
        >
          {navItems.map((item) => (
            <button
              key={item.view}
              type="button"
              onClick={() => navigateTo(item.view)}
              style={
                isCompact
                  ? tabButtonStyle(activeView === item.view)
                  : navButtonStyle(activeView === item.view)
              }
            >
              {isCompact ? <NavIcon view={item.view} /> : null}
              {isCompact ? <span>{TAB_LABELS[item.view]}</span> : item.label}
            </button>
          ))}
        </nav>
        <ConnectionLostBanner connectionLost={activeConnectionLost} />
        <main style={mainStyle(isCompact, true)}>
          {activeView === 'week' ? <WeekPlannerView {...weekPlanner} viewport={viewport} /> : null}
          {activeView === 'library' ? <LibraryView {...library} viewport={viewport} /> : null}
          {activeView === 'rules' ? <RulesView {...rules} viewport={viewport} /> : null}
          {activeView === 'shoppingList' ? (
            <ShoppingListView {...shoppingList} viewport={viewport} />
          ) : null}
          {activeView === 'summary' ? <SummaryView {...summary} viewport={viewport} /> : null}
        </main>
      </div>
    );
  }

  return null; // Unreachable: authenticated always carries a User or Admin role.
}

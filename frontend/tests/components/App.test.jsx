// @vitest-environment jsdom
// Mocks every hook + child view/screen component: proves only App.jsx's own
// job - which shell mounts, which view, which poll feeds the banner, logout
// (R23/R30-R32, design.md section 5/5a). See progress/impl_frontend_spa.md.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mockViewport } from '../helpers/viewport.js';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';

vi.mock('../../src/hooks/useWeekPlanner.js', () => ({ useWeekPlanner: vi.fn() }));
vi.mock('../../src/hooks/useLibrary.js', () => ({ useLibrary: vi.fn() }));
vi.mock('../../src/hooks/useRules.js', () => ({ useRules: vi.fn() }));
vi.mock('../../src/hooks/useShoppingList.js', () => ({ useShoppingList: vi.fn() }));
vi.mock('../../src/hooks/useSummary.js', () => ({ useSummary: vi.fn() }));
vi.mock('../../src/hooks/useSession.js', () => ({ useSession: vi.fn() }));
vi.mock('../../src/hooks/useLoginForm.js', () => ({ useLoginForm: vi.fn() }));
vi.mock('../../src/hooks/useSetPasswordForm.js', () => ({ useSetPasswordForm: vi.fn() }));
vi.mock('../../src/hooks/useAdminAccounts.js', () => ({ useAdminAccounts: vi.fn() }));

vi.mock('../../src/components/WeekPlannerView.jsx', () => ({
  WeekPlannerView: () => <p>WEEK_VIEW_MARKER</p>,
}));
vi.mock('../../src/components/LibraryView.jsx', () => ({
  LibraryView: () => <p>LIBRARY_VIEW_MARKER</p>,
}));
vi.mock('../../src/components/RulesView.jsx', () => ({
  RulesView: () => <p>RULES_VIEW_MARKER</p>,
}));
vi.mock('../../src/components/ShoppingListView.jsx', () => ({
  ShoppingListView: () => <p>SHOPPING_LIST_VIEW_MARKER</p>,
}));
vi.mock('../../src/components/SummaryView.jsx', () => ({
  SummaryView: () => <p>SUMMARY_VIEW_MARKER</p>,
}));
vi.mock('../../src/components/LoginView.jsx', () => ({
  LoginView: () => <p>LOGIN_VIEW_MARKER</p>,
}));
vi.mock('../../src/components/SetPasswordView.jsx', () => ({
  SetPasswordView: () => <p>SET_PASSWORD_VIEW_MARKER</p>,
}));
// Renders actingUserId into the marker so a dropped App.jsx prop wiring
// (fix round 1 finding 2) fails this file's own assertions, not a mock detail.
vi.mock('../../src/components/AdminAccountsView.jsx', () => ({
  AdminAccountsView: ({ actingUserId }) => <p>{`ADMIN_ACCOUNTS_VIEW_MARKER:${actingUserId}`}</p>,
}));

import { App } from '../../src/components/App.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { useWeekPlanner } from '../../src/hooks/useWeekPlanner.js';
import { useLibrary } from '../../src/hooks/useLibrary.js';
import { useRules } from '../../src/hooks/useRules.js';
import { useShoppingList } from '../../src/hooks/useShoppingList.js';
import { useSummary } from '../../src/hooks/useSummary.js';
import { useSession } from '../../src/hooks/useSession.js';
import { useLoginForm } from '../../src/hooks/useLoginForm.js';
import { useSetPasswordForm } from '../../src/hooks/useSetPasswordForm.js';
import { useAdminAccounts } from '../../src/hooks/useAdminAccounts.js';

beforeEach(() => {
  mockViewport();
  window.history.replaceState(null, '', '/'); // the view hash persists across tests (R48)
});
afterEach(cleanup);

const USER_SESSION = { status: 'authenticated', role: 'User' };

function stubHooks({ connectionLost = {}, session = USER_SESSION, logout = vi.fn() } = {}) {
  useWeekPlanner.mockReturnValue({ connectionLost: connectionLost.week ?? false });
  useLibrary.mockReturnValue({ connectionLost: connectionLost.library ?? false });
  useRules.mockReturnValue({ connectionLost: connectionLost.rules ?? false });
  useShoppingList.mockReturnValue({ connectionLost: connectionLost.shoppingList ?? false });
  useSummary.mockReturnValue({ connectionLost: connectionLost.summary ?? false });
  useSession.mockReturnValue({ session, login: vi.fn(), setPassword: vi.fn(), logout });
  useLoginForm.mockReturnValue({});
  useSetPasswordForm.mockReturnValue({ status: session.status });
  useAdminAccounts.mockReturnValue({ accounts: [], isLoading: false });
  return { logout };
}

const MARKERS = {
  week: 'WEEK_VIEW_MARKER',
  library: 'LIBRARY_VIEW_MARKER',
  rules: 'RULES_VIEW_MARKER',
  shoppingList: 'SHOPPING_LIST_VIEW_MARKER',
  summary: 'SUMMARY_VIEW_MARKER',
};
describe('App', () => {
  it('mounts SummaryView by default (User shell, R58)', () => {
    stubHooks();
    render(<App />);

    expect(screen.getByText(MARKERS.summary)).not.toBeNull();
    Object.values(MARKERS)
      .filter((marker) => marker !== MARKERS.summary)
      .forEach((marker) => expect(screen.queryByText(marker)).toBeNull());
  });

  it('navigating mounts exactly the clicked view, none of the other four', () => {
    stubHooks();
    render(<App />);

    for (const [view, label] of [
      ['library', MESSAGES.NAV_LIBRARY],
      ['rules', MESSAGES.NAV_RULES],
      ['shoppingList', MESSAGES.NAV_SHOPPING_LIST],
      ['summary', MESSAGES.NAV_SUMMARY],
      ['week', MESSAGES.NAV_WEEK],
    ]) {
      fireEvent.click(screen.getByText(label));

      expect(screen.getByText(MARKERS[view])).not.toBeNull();
      Object.entries(MARKERS)
        .filter(([otherView]) => otherView !== view)
        .forEach(([, marker]) => expect(screen.queryByText(marker)).toBeNull());
    }
  });

  it('lays the navigation pills out in a wrapping flex row (R3)', () => {
    stubHooks();
    render(<App />);

    const nav = screen.getByText(MESSAGES.NAV_WEEK).parentElement;
    expect(nav.style.display).toBe('flex');
    expect(nav.style.flexWrap).toBe('wrap');
  });

  it('renders the connection-lost banner when the ACTIVE view reports connectionLost (FR-RT-03)', () => {
    stubHooks({ connectionLost: { summary: true } });
    render(<App />);

    expect(screen.getByText(MESSAGES.CONNECTION_LOST)).not.toBeNull();
  });

  it('does not render the banner when a non-active view is the one reporting connectionLost', () => {
    stubHooks({ connectionLost: { library: true } });
    render(<App />);

    expect(screen.queryByText(MESSAGES.CONNECTION_LOST)).toBeNull();

    fireEvent.click(screen.getByText(MESSAGES.NAV_LIBRARY));
    expect(screen.getByText(MESSAGES.CONNECTION_LOST)).not.toBeNull();
  });

  // App shell fix round 1, finding 1: mounting must not start 5 permanent
  // polling loops - only the active view's hook gets `active: true`.
  it('passes active: true to only the active view hook, active: false to the other 4', () => {
    stubHooks();
    render(<App />);

    expect(useWeekPlanner).toHaveBeenLastCalledWith({ active: false, signedIn: true });
    expect(useLibrary).toHaveBeenLastCalledWith({ active: false });
    expect(useRules).toHaveBeenLastCalledWith({ active: false });
    expect(useShoppingList).toHaveBeenLastCalledWith({ active: false });
    expect(useSummary).toHaveBeenLastCalledWith({ active: true });
  });

  it('navigating flips active: true/false to match the newly active view', () => {
    stubHooks();
    render(<App />);

    fireEvent.click(screen.getByText(MESSAGES.NAV_LIBRARY));

    expect(useWeekPlanner).toHaveBeenLastCalledWith({ active: false, signedIn: true });
    expect(useLibrary).toHaveBeenLastCalledWith({ active: true });
    expect(useRules).toHaveBeenLastCalledWith({ active: false });
    expect(useShoppingList).toHaveBeenLastCalledWith({ active: false });
    expect(useSummary).toHaveBeenLastCalledWith({ active: false });
  });

  // Render-branch wiring (T59): session.status/role picks exactly one shell,
  // never a fallthrough into the wrong one.
  it('renders a loading state while the mount-time probe is in flight, no shell mounted (R23)', () => {
    stubHooks({ session: { status: 'loading' } });
    render(<App />);

    expect(screen.getByText(MESSAGES.LOADING_STATE_DEFAULT)).not.toBeNull();
    [
      ...Object.values(MARKERS),
      'LOGIN_VIEW_MARKER',
      'SET_PASSWORD_VIEW_MARKER',
      'ADMIN_ACCOUNTS_VIEW_MARKER',
    ].forEach((marker) => expect(screen.queryByText(marker)).toBeNull());
  });

  it('renders LoginView when anonymous, no other shell mounted (R23)', () => {
    stubHooks({ session: { status: 'anonymous' } });
    render(<App />);

    expect(screen.getByText('LOGIN_VIEW_MARKER')).not.toBeNull();
    [...Object.values(MARKERS), 'SET_PASSWORD_VIEW_MARKER', 'ADMIN_ACCOUNTS_VIEW_MARKER'].forEach(
      (marker) => expect(screen.queryByText(marker)).toBeNull(),
    );
  });

  it('renders SetPasswordView when passwordResetPending, no other shell mounted (R26)', () => {
    stubHooks({ session: { status: 'passwordResetPending' } });
    render(<App />);

    expect(screen.getByText('SET_PASSWORD_VIEW_MARKER')).not.toBeNull();
    [...Object.values(MARKERS), 'LOGIN_VIEW_MARKER', 'ADMIN_ACCOUNTS_VIEW_MARKER'].forEach(
      (marker) => expect(screen.queryByText(marker)).toBeNull(),
    );
  });

  it('renders AdminAccountsView only for an authenticated Admin, no meal-planning nav (R30)', () => {
    stubHooks({ session: { status: 'authenticated', role: 'Admin', userId: 'admin-1' } });
    render(<App />);

    // Traces session.userId through App.jsx's actingUserId={session.userId} wiring (fix round 1 finding 2).
    expect(screen.getByText('ADMIN_ACCOUNTS_VIEW_MARKER:admin-1')).not.toBeNull();
    Object.values(MARKERS).forEach((marker) => expect(screen.queryByText(marker)).toBeNull());
    expect(screen.queryByText('LOGIN_VIEW_MARKER')).toBeNull();
    [MESSAGES.NAV_WEEK, MESSAGES.NAV_LIBRARY, MESSAGES.NAV_RULES].forEach((label) =>
      expect(screen.queryByText(label)).toBeNull(),
    );
  });

  it('renders the 5-view User shell with no admin nav target reachable (R31)', () => {
    stubHooks({ session: USER_SESSION });
    render(<App />);

    expect(screen.getByText(MARKERS.summary)).not.toBeNull();
    expect(screen.queryByText('ADMIN_ACCOUNTS_VIEW_MARKER')).toBeNull();
    expect(screen.queryByText(MESSAGES.ADMIN_ACCOUNTS_VIEW_TITLE)).toBeNull();
  });

  it('logout control renders in the User shell and calls session.logout on click (R32)', () => {
    const { logout } = stubHooks({ session: USER_SESSION });
    render(<App />);

    fireEvent.click(screen.getByText(MESSAGES.APP_LOGOUT));
    expect(logout).toHaveBeenCalledTimes(1);
  });

  it('logout control renders in the Admin shell and calls session.logout on click (R32)', () => {
    const { logout } = stubHooks({ session: { status: 'authenticated', role: 'Admin' } });
    render(<App />);

    fireEvent.click(screen.getByText(MESSAGES.APP_LOGOUT));
    expect(logout).toHaveBeenCalledTimes(1);
  });
});

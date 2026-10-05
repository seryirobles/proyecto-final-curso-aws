// @vitest-environment jsdom
// R42-R44: App sizes the logout button and passes `viewport` to every view.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { mockViewport } from '../helpers/viewport.js';

vi.mock('../../src/hooks/useWeekPlanner.js', () => ({ useWeekPlanner: vi.fn() }));
vi.mock('../../src/hooks/useLibrary.js', () => ({ useLibrary: vi.fn() }));
vi.mock('../../src/hooks/useRules.js', () => ({ useRules: vi.fn() }));
vi.mock('../../src/hooks/useShoppingList.js', () => ({ useShoppingList: vi.fn() }));
vi.mock('../../src/hooks/useSummary.js', () => ({ useSummary: vi.fn() }));
vi.mock('../../src/hooks/useSession.js', () => ({ useSession: vi.fn() }));
vi.mock('../../src/hooks/useLoginForm.js', () => ({ useLoginForm: vi.fn() }));
vi.mock('../../src/hooks/useSetPasswordForm.js', () => ({ useSetPasswordForm: vi.fn() }));
vi.mock('../../src/hooks/useAdminAccounts.js', () => ({ useAdminAccounts: vi.fn() }));
vi.mock('../../src/components/WeekPlannerView.jsx', () => ({ WeekPlannerView: () => null }));
vi.mock('../../src/components/SummaryView.jsx', () => ({ SummaryView: () => null }));
vi.mock('../../src/components/LibraryView.jsx', () => ({
  LibraryView: ({ viewport }) => <p>{`LIBRARY:${viewport}`}</p>,
}));
vi.mock('../../src/components/RulesView.jsx', () => ({
  RulesView: ({ viewport }) => <p>{`RULES:${viewport}`}</p>,
}));
vi.mock('../../src/components/ShoppingListView.jsx', () => ({
  ShoppingListView: ({ viewport }) => <p>{`SHOPPING:${viewport}`}</p>,
}));
vi.mock('../../src/components/AdminAccountsView.jsx', () => ({
  AdminAccountsView: ({ viewport }) => <p>{`ADMIN:${viewport}`}</p>,
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

function signIn(role) {
  useSession.mockReturnValue({
    session: { status: 'authenticated', role },
    login: vi.fn(),
    setPassword: vi.fn(),
    logout: vi.fn(),
  });
}

beforeEach(() => {
  window.scrollTo = vi.fn();
  [useWeekPlanner, useLibrary, useRules, useShoppingList, useSummary].forEach((h) =>
    h.mockReturnValue({ connectionLost: false }),
  );
  useLoginForm.mockReturnValue({});
  useSetPasswordForm.mockReturnValue({});
  useAdminAccounts.mockReturnValue({ accounts: [], isLoading: false });
});
afterEach(cleanup);

describe('App touch targets', () => {
  it.each([
    [375, '44px'],
    [700, '44px'],
    [768, '24px'],
    [1440, '24px'],
  ])('logout button at %i px', (width, px) => {
    signIn('User');
    mockViewport(width);
    render(<App />);
    const logout = screen.getByRole('button', { name: MESSAGES.APP_LOGOUT });
    expect([logout.style.minHeight, logout.style.minWidth]).toEqual([px, px]);
  });

  it('sizes the Admin logout button', () => {
    signIn('Admin');
    mockViewport(375);
    render(<App />);
    const logout = screen.getByRole('button', { name: MESSAGES.APP_LOGOUT });
    expect(logout.style.minHeight).toBe('44px');
    expect(screen.getByText('ADMIN:compact')).not.toBeNull();
  });

  it('passes viewport to Library, Rules and Shopping', () => {
    signIn('User');
    mockViewport(375);
    render(<App />);
    const expected = [
      [MESSAGES.NAV_LIBRARY, 'LIBRARY:compact'],
      [MESSAGES.NAV_RULES, 'RULES:compact'],
      [MESSAGES.NAV_SHOPPING_LIST_SHORT, 'SHOPPING:compact'],
    ];
    expected.forEach(([nav, text]) => {
      fireEvent.click(screen.getByRole('button', { name: nav }));
      expect(screen.getByText(text)).not.toBeNull();
    });
  });
});

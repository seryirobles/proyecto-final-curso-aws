// @vitest-environment jsdom
// Tab bar and pills render Resumen first (frontend_ux_phase2 R67, R68).
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup, within } from '@testing-library/react';
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
vi.mock('../../src/components/AdminAccountsView.jsx', () => ({
  AdminAccountsView: () => <p>A</p>,
}));
vi.mock('../../src/components/SummaryView.jsx', () => ({ SummaryView: () => <p>S</p> }));

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

function stub(session) {
  [useWeekPlanner, useLibrary, useRules, useShoppingList, useSummary].forEach((h) =>
    h.mockReturnValue({ connectionLost: false }),
  );
  useSession.mockReturnValue({ session, login: vi.fn(), setPassword: vi.fn(), logout: vi.fn() });
  useLoginForm.mockReturnValue({});
  useSetPasswordForm.mockReturnValue({});
  useAdminAccounts.mockReturnValue({ accounts: [], isLoading: false });
}

const USER = { status: 'authenticated', role: 'User' };
const names = () =>
  within(screen.getByRole('navigation'))
    .getAllByRole('button')
    .map((b) => b.textContent);

beforeEach(() => {
  window.history.replaceState(null, '', '/');
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

describe('App nav order', () => {
  it('tab bar (compact) lists Resumen first, short shopping label (R67)', () => {
    mockViewport(375);
    stub(USER);
    render(<App />);
    expect(names()).toEqual([
      MESSAGES.NAV_SUMMARY,
      MESSAGES.NAV_WEEK,
      MESSAGES.NAV_LIBRARY,
      MESSAGES.NAV_RULES,
      MESSAGES.NAV_SHOPPING_LIST_SHORT,
    ]);
  });

  it('pills (wide) list Resumen first (R68)', () => {
    mockViewport(1440);
    stub(USER);
    render(<App />);
    expect(names()).toEqual([
      MESSAGES.NAV_SUMMARY,
      MESSAGES.NAV_WEEK,
      MESSAGES.NAV_LIBRARY,
      MESSAGES.NAV_RULES,
      MESSAGES.NAV_SHOPPING_LIST,
    ]);
  });

  it('the Admin shell renders no nav', () => {
    mockViewport(1440);
    stub({ status: 'authenticated', role: 'Admin', userId: 'a' });
    render(<App />);
    expect(screen.queryByRole('navigation')).toBeNull();
  });
});

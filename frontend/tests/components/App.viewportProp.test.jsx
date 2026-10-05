// @vitest-environment jsdom
// R6: App passes useViewport's tier to the Week and Summary views.
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
vi.mock('../../src/components/WeekPlannerView.jsx', () => ({
  WeekPlannerView: ({ viewport }) => <p>{`WEEK:${viewport}`}</p>,
}));
vi.mock('../../src/components/SummaryView.jsx', () => ({
  SummaryView: ({ viewport }) => <p>{`SUMMARY:${viewport}`}</p>,
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
  window.history.replaceState(null, '', '/'); // the view hash persists across tests (R48)
  window.scrollTo = vi.fn();
  [useWeekPlanner, useLibrary, useRules, useShoppingList, useSummary].forEach((h) =>
    h.mockReturnValue({ connectionLost: false }),
  );
  useSession.mockReturnValue({
    session: { status: 'authenticated', role: 'User' },
    login: vi.fn(),
    setPassword: vi.fn(),
    logout: vi.fn(),
  });
  useLoginForm.mockReturnValue({});
  useSetPasswordForm.mockReturnValue({});
  useAdminAccounts.mockReturnValue({ accounts: [], isLoading: false });
});
afterEach(cleanup);

describe('App viewport prop', () => {
  it.each([
    [375, 'compact', MESSAGES.NAV_SHOPPING_LIST_SHORT],
    [1440, 'wide', MESSAGES.NAV_SHOPPING_LIST],
  ])('passes %i px (%s) to Week and Summary', (width, tier, shopping) => {
    mockViewport(width);
    render(<App />);
    expect(screen.getByText(`WEEK:${tier}`)).not.toBeNull();

    fireEvent.click(screen.getByRole('button', { name: MESSAGES.NAV_SUMMARY }));

    expect(screen.getByText(`SUMMARY:${tier}`)).not.toBeNull();
    expect(screen.getByRole('button', { name: shopping })).not.toBeNull();
  });
});

// @vitest-environment jsdom
// Issue blank-screen-after-login (E1, E2): POST /v1/session answers with the
// backend's wire role ("user"/"admin"), and the shell must mount from it
// without a page reload.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

// Only the session state machine is under test; the view hooks and the two
// shell views are stubbed, as in App.test.jsx.
vi.mock('../../src/hooks/useWeekPlanner.js', () => ({
  useWeekPlanner: () => ({ connectionLost: false }),
}));
vi.mock('../../src/hooks/useLibrary.js', () => ({ useLibrary: () => ({ connectionLost: false }) }));
vi.mock('../../src/hooks/useRules.js', () => ({ useRules: () => ({ connectionLost: false }) }));
vi.mock('../../src/hooks/useShoppingList.js', () => ({
  useShoppingList: () => ({ connectionLost: false }),
}));
vi.mock('../../src/hooks/useSummary.js', () => ({ useSummary: () => ({ connectionLost: false }) }));
vi.mock('../../src/hooks/useAdminAccounts.js', () => ({
  useAdminAccounts: () => ({ accounts: [], isLoading: false }),
}));
vi.mock('../../src/components/WeekPlannerView.jsx', () => ({
  WeekPlannerView: () => <p>WEEK_VIEW_MARKER</p>,
}));
vi.mock('../../src/components/AdminAccountsView.jsx', () => ({
  AdminAccountsView: () => <p>ADMIN_ACCOUNTS_VIEW_MARKER</p>,
}));

import { apiFetch, ApiError } from '../../src/api/client.js';
import { App } from '../../src/components/App.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// No cookie yet: the mount probe fails, so the app starts anonymous.
function serveLogin(loginBody) {
  apiFetch.mockImplementation((url) =>
    url === '/v1/session'
      ? Promise.resolve(loginBody)
      : Promise.reject(new ApiError({ status: 401, code: 'SESSION_EXPIRED', detail: 'x' })),
  );
}

async function logIn() {
  await waitFor(() => expect(screen.getByText(MESSAGES.LOGIN_SUBMIT)).not.toBeNull());
  fireEvent.change(screen.getByLabelText(MESSAGES.LOGIN_USERNAME_LABEL), {
    target: { value: 'ana' },
  });
  fireEvent.change(screen.getByLabelText(MESSAGES.LOGIN_PASSWORD_LABEL), {
    target: { value: 's3cret1234' },
  });
  fireEvent.click(screen.getByText(MESSAGES.LOGIN_SUBMIT));
}

describe('App after a successful login', () => {
  it('mounts the meal-planning shell for a user with no pending password change (E1)', async () => {
    serveLogin({ userId: 'u-1', role: 'user', passwordResetRequired: false });
    render(<App />);

    await logIn();

    await waitFor(() => expect(screen.getByText('WEEK_VIEW_MARKER')).not.toBeNull());
    expect(screen.getByText(MESSAGES.NAV_WEEK)).not.toBeNull();
    expect(screen.queryByText(MESSAGES.LOGIN_SUBMIT)).toBeNull();
  });

  it('mounts the admin shell for an admin with no pending password change (E2)', async () => {
    serveLogin({ userId: 'a-1', role: 'admin', passwordResetRequired: false });
    render(<App />);

    await logIn();

    await waitFor(() => expect(screen.getByText('ADMIN_ACCOUNTS_VIEW_MARKER')).not.toBeNull());
    expect(screen.queryByText('WEEK_VIEW_MARKER')).toBeNull();
  });

  it('still routes a pending password change to the set-password screen (E1 boundary)', async () => {
    serveLogin({ userId: 'u-2', role: 'user', passwordResetRequired: true });
    render(<App />);

    await logIn();

    await waitFor(() => expect(screen.getByText(MESSAGES.SET_PASSWORD_SUBMIT)).not.toBeNull());
    expect(screen.queryByText('WEEK_VIEW_MARKER')).toBeNull();
  });
});

// @vitest-environment jsdom
// Issue blank-screen-after-login, blast radius (E3, E4): GET /v1/users answers
// with the same wire role ("user"/"admin"), so the account list must label and
// gate its rows from it.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup, waitFor } from '@testing-library/react';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch } from '../../src/api/client.js';
import { useAdminAccounts } from '../../src/hooks/useAdminAccounts.js';
import { AdminAccountsView } from '../../src/components/AdminAccountsView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Verbatim shape of encode_account (backend/lambda_api/.../serialization.py).
const WIRE_USERS = {
  users: [
    { userId: 'a-1', username: 'sofia', role: 'admin', passwordResetRequired: false },
    { userId: 'u-1', username: 'ana', role: 'user', passwordResetRequired: false },
  ],
};

// The hook owns the fetch, the view owns the markup: the seam under test.
function AdminAccountsHarness() {
  const accounts = useAdminAccounts();
  return <AdminAccountsView {...accounts} actingUserId="a-1" />;
}

describe('the admin account list fed by the real wire payload', () => {
  it('labels each role in Castilian Spanish, never the raw wire value (E3)', async () => {
    apiFetch.mockResolvedValue(WIRE_USERS);
    render(<AdminAccountsHarness />);

    await waitFor(() => expect(screen.getByText('ana')).not.toBeNull());
    expect(screen.getByText('Administrador')).not.toBeNull();
    expect(screen.getByText('Usuario')).not.toBeNull();
    expect(screen.queryByText('admin')).toBeNull();
    expect(screen.queryByText('user')).toBeNull();
  });

  it('offers the remove control on the user row only, never on the admin row (E4)', async () => {
    apiFetch.mockResolvedValue(WIRE_USERS);
    render(<AdminAccountsHarness />);

    await waitFor(() => expect(screen.getByText('ana')).not.toBeNull());
    const removeControls = screen.getAllByText(MESSAGES.ADMIN_ACCOUNTS_REMOVE);
    expect(removeControls).toHaveLength(1);
    expect(removeControls[0].closest('li').textContent).toContain('ana');
  });
});

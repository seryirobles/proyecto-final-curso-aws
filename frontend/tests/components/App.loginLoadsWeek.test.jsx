// @vitest-environment jsdom
// Issue stuck-loading-after-login (E1, E2): the app mounts with no session,
// the user logs in, and the week view must load without a page reload.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch, ApiError } from '../../src/api/client.js';
import { App } from '../../src/components/App.jsx';
import { MESSAGES } from '../../src/messages/index.js';

const EXPIRED_DETAIL = 'Tu sesión ha caducado.';
const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

// Every read fails SESSION_EXPIRED until POST /v1/session succeeds.
function serveSessionThenData() {
  let loggedIn = false;
  apiFetch.mockImplementation((url) => {
    if (url === '/v1/session') {
      loggedIn = true;
      return Promise.resolve({ userId: 'u-1', role: 'user', passwordResetRequired: false });
    }
    if (!loggedIn) {
      return Promise.reject(
        new ApiError({ status: 403, code: 'SESSION_EXPIRED', detail: EXPIRED_DETAIL }),
      );
    }
    return Promise.resolve(url === '/v1/live-weeks' ? LIVE_WEEKS : {});
  });
  globalThis.fetch = vi.fn(async () => ({
    status: 200,
    headers: new Headers({ ETag: '"1"' }),
    json: async () => ({ weekId: '2026-W34', slots: [] }),
  }));
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

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('App: login from a cold, session-less mount', () => {
  it('loads the week view instead of staying on the loading state (E1)', async () => {
    serveSessionThenData();
    render(<App />);

    await logIn();

    await waitFor(() =>
      expect(screen.getAllByText(MESSAGES.WEEK_PLANNER_ADD_CANDIDATE)).toHaveLength(14),
    );
    expect(screen.queryByText(MESSAGES.LOADING_STATE_DEFAULT)).toBeNull();
  });

  it('does not show the pre-login session error on the loaded week view (E2)', async () => {
    serveSessionThenData();
    render(<App />);

    await logIn();

    await waitFor(() =>
      expect(screen.getAllByText(MESSAGES.WEEK_PLANNER_ADD_CANDIDATE)).toHaveLength(14),
    );
    expect(screen.queryByText(EXPIRED_DETAIL)).toBeNull();
  });
});

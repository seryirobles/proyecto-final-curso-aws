// @vitest-environment jsdom
// Issue stuck-loading-after-login, blast radius (E3, E4): the summary and the
// shopping-list scope read live-weeks the same way as the week view.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});

import { apiFetch, ApiError } from '../../src/api/client.js';
import { App } from '../../src/components/App.jsx';
import { MESSAGES } from '../../src/messages/index.js';

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
      return Promise.reject(new ApiError({ status: 403, code: 'SESSION_EXPIRED', detail: 'x' }));
    }
    return Promise.resolve(url === '/v1/live-weeks' ? LIVE_WEEKS : {});
  });
  const bodies = {
    '/v1/weeks/2026-W34': { weekId: '2026-W34', slots: [] },
    '/v1/weeks/2026-W34/summary': { weekId: '2026-W34', meals: [] },
    '/v1/shopping-list': { items: [] },
  };
  globalThis.fetch = vi.fn(async (url) => ({
    status: 200,
    headers: new Headers({ ETag: '"1"' }),
    json: async () => bodies[url] ?? {},
  }));
}

async function logInAndOpen(navLabel) {
  await waitFor(() => expect(screen.getByText(MESSAGES.LOGIN_SUBMIT)).not.toBeNull());
  fireEvent.change(screen.getByLabelText(MESSAGES.LOGIN_USERNAME_LABEL), {
    target: { value: 'ana' },
  });
  fireEvent.change(screen.getByLabelText(MESSAGES.LOGIN_PASSWORD_LABEL), {
    target: { value: 's3cret1234' },
  });
  fireEvent.click(screen.getByText(MESSAGES.LOGIN_SUBMIT));
  await waitFor(() => expect(screen.getByText(navLabel)).not.toBeNull());
  fireEvent.click(screen.getByText(navLabel));
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('App: other live-weeks readers after a cold login', () => {
  it('loads the summary view instead of staying on the loading state (E3)', async () => {
    serveSessionThenData();
    render(<App />);

    await logInAndOpen(MESSAGES.NAV_SUMMARY);

    await waitFor(() => expect(screen.getByText(MESSAGES.SUMMARY_VIEW_TITLE)).not.toBeNull());
    expect(screen.queryByText(MESSAGES.LOADING_STATE_DEFAULT)).toBeNull();
  });

  it('labels the shopping-list resync scope with both live weeks (E4)', async () => {
    serveSessionThenData();
    render(<App />);

    await logInAndOpen(MESSAGES.NAV_SHOPPING_LIST);

    await waitFor(() => expect(screen.getByText(MESSAGES.SHOPPING_LIST_RESYNC)).not.toBeNull());
    await waitFor(() => expect(screen.getByText(MESSAGES.WEEK_LABEL_NEXT)).not.toBeNull());
    expect(screen.getByText(MESSAGES.WEEK_LABEL_CURRENT)).not.toBeNull();
  });
});

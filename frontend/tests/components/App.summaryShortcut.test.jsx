// @vitest-environment jsdom
// Summary landing view and its week shortcut through the real App (frontend_ux_phase2 R58, R62).
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
  WeekPlannerView: () => <p>WEEK_VIEW_MARKER</p>,
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

let push;

beforeEach(() => {
  mockViewport();
  window.history.replaceState(null, '', '/');
  window.scrollTo = vi.fn();
  [useWeekPlanner, useLibrary, useRules, useShoppingList].forEach((h) =>
    h.mockReturnValue({ connectionLost: false }),
  );
  useSummary.mockReturnValue({
    connectionLost: false,
    isLoading: false,
    week: null,
    summary: { days: [], isEmpty: true },
  });
  useSession.mockReturnValue({
    session: { status: 'authenticated', role: 'User' },
    login: vi.fn(),
    setPassword: vi.fn(),
    logout: vi.fn(),
  });
  useLoginForm.mockReturnValue({});
  useSetPasswordForm.mockReturnValue({});
  useAdminAccounts.mockReturnValue({ accounts: [], isLoading: false });
  push = vi.spyOn(window.history, 'pushState');
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('App summary landing and shortcut', () => {
  it('lands on the summary with #/resumen (R58)', () => {
    render(<App />);
    expect(screen.getByText(MESSAGES.SUMMARY_VIEW_TITLE)).not.toBeNull();
    expect(window.location.hash).toBe('#/resumen');
    expect(push).not.toHaveBeenCalled();
  });

  it('the shortcut opens the week with a single pushState and disappears (R62)', () => {
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: MESSAGES.SUMMARY_EDIT_WEEK }));

    expect(screen.getByText('WEEK_VIEW_MARKER')).not.toBeNull();
    expect(push).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith(null, '', '#/semana');
    expect(screen.queryByRole('button', { name: MESSAGES.SUMMARY_EDIT_WEEK })).toBeNull();
  });
});

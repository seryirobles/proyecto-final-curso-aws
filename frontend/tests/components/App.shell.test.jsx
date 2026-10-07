// @vitest-environment jsdom
// Shell layout per viewport tier (frontend_ux_phase2 R8-R19). Views are stubbed.
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
vi.mock('../../src/components/WeekPlannerView.jsx', () => ({ WeekPlannerView: () => <p>W</p> }));
vi.mock('../../src/components/LibraryView.jsx', () => ({ LibraryView: () => <p>L</p> }));
vi.mock('../../src/components/RulesView.jsx', () => ({ RulesView: () => <p>R</p> }));
vi.mock('../../src/components/ShoppingListView.jsx', () => ({ ShoppingListView: () => <p>S</p> }));
vi.mock('../../src/components/SummaryView.jsx', () => ({ SummaryView: () => <p>M</p> }));
vi.mock('../../src/components/AdminAccountsView.jsx', () => ({
  AdminAccountsView: () => <p>A</p>,
}));

import { App } from '../../src/components/App.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { tokens } from '../../src/tokens/index.js';
import { useWeekPlanner } from '../../src/hooks/useWeekPlanner.js';
import { useLibrary } from '../../src/hooks/useLibrary.js';
import { useRules } from '../../src/hooks/useRules.js';
import { useShoppingList } from '../../src/hooks/useShoppingList.js';
import { useSummary } from '../../src/hooks/useSummary.js';
import { useSession } from '../../src/hooks/useSession.js';
import { useLoginForm } from '../../src/hooks/useLoginForm.js';
import { useSetPasswordForm } from '../../src/hooks/useSetPasswordForm.js';
import { useAdminAccounts } from '../../src/hooks/useAdminAccounts.js';

function stub(session = { status: 'authenticated', role: 'User' }) {
  [useWeekPlanner, useLibrary, useRules, useShoppingList, useSummary].forEach((h) =>
    h.mockReturnValue({ connectionLost: false }),
  );
  useSession.mockReturnValue({ session, login: vi.fn(), setPassword: vi.fn(), logout: vi.fn() });
  useLoginForm.mockReturnValue({});
  useSetPasswordForm.mockReturnValue({});
  useAdminAccounts.mockReturnValue({ accounts: [], isLoading: false });
}

beforeEach(() => {
  window.scrollTo = vi.fn();
});
afterEach(cleanup);

const px = (value) => Number.parseInt(value, 10);
const TERRA_RGB = 'rgb(46, 107, 52)';

describe('App shell, compact (tab bar)', () => {
  beforeEach(() => {
    mockViewport(375);
    stub();
  });

  it('renders a fixed bottom nav padded by the safe-area inset (R8, R12)', () => {
    render(<App />);
    const nav = screen.getByRole('navigation');
    expect(nav.style.position).toBe('fixed');
    expect(nav.style.bottom).toBe('0px');
    // A unitless 0 in calc() is invalid next to a length, so require a length operand.
    expect(nav.style.paddingBottom).toMatch(
      /calc\(\s*0px\s*\+\s*env\(safe-area-inset-bottom\)\s*\)/,
    );
  });

  it('has five buttons named by their visible text, short shopping label (R10)', () => {
    render(<App />);
    [
      MESSAGES.NAV_WEEK,
      MESSAGES.NAV_LIBRARY,
      MESSAGES.NAV_RULES,
      MESSAGES.NAV_SHOPPING_LIST_SHORT,
      MESSAGES.NAV_SUMMARY,
    ].forEach((name) => expect(screen.getByRole('button', { name })).not.toBeNull());
  });

  it('gives each tab button a min height of at least 48 px from a token (R11)', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: MESSAGES.NAV_WEEK });
    expect(button.style.minHeight).toBe(tokens.layout.tabBarHeight);
    expect(px(button.style.minHeight)).toBeGreaterThanOrEqual(48);
  });

  it('pads main by the tab bar height (R13)', () => {
    render(<App />);
    const main = screen.getByRole('main');
    expect(main.style.paddingBottom).toContain(tokens.layout.tabBarHeight);
    expect(main.style.paddingBottom).toContain('env(safe-area-inset-bottom)');
  });

  it('marks the active tab bold with a terra border (R14)', () => {
    render(<App />);
    const active = screen.getByRole('button', { name: MESSAGES.NAV_SUMMARY });
    const other = screen.getByRole('button', { name: MESSAGES.NAV_RULES });
    expect(active.style.fontWeight).toBe('700');
    expect(active.style.border).toContain(TERRA_RGB);
    expect(other.style.fontWeight).not.toBe('700');
  });
});

describe('App shell, medium (pill row)', () => {
  beforeEach(() => {
    mockViewport(1000);
    stub();
  });

  it('renders the nav as a non-fixed row after the header (R9)', () => {
    render(<App />);
    const nav = screen.getByRole('navigation');
    const header = screen.getByRole('heading', { level: 1 }).parentElement;
    expect(nav.style.position).not.toBe('fixed');
    expect(
      header.compareDocumentPosition(nav) & window.Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: MESSAGES.NAV_SHOPPING_LIST })).not.toBeNull();
  });

  it('does not pad main for a tab bar (R13)', () => {
    render(<App />);
    expect(screen.getByRole('main').style.paddingBottom).not.toContain(tokens.layout.tabBarHeight);
  });

  it('marks the active pill bold with a terra border (R14)', () => {
    render(<App />);
    const active = screen.getByRole('button', { name: MESSAGES.NAV_SUMMARY });
    expect(active.style.fontWeight).toBe('700');
    expect(active.style.border).toContain(TERRA_RGB);
  });
});

describe('App shell, common', () => {
  it('centres main within contentMax (R16)', () => {
    mockViewport(1440);
    stub();
    render(<App />);
    const main = screen.getByRole('main');
    expect(main.style.maxWidth).toBe(tokens.layout.contentMax);
    expect(main.style.margin).toBe('0px auto');
  });

  it.each([
    ['User', { status: 'authenticated', role: 'User' }],
    ['Admin', { status: 'authenticated', role: 'Admin', userId: 'a' }],
  ])('keeps the %s header sticky to the top (R15)', (_name, session) => {
    mockViewport(1440);
    stub(session);
    render(<App />);
    const header = screen.getByRole('heading', { level: 1 }).parentElement;
    expect(header.style.position).toBe('sticky');
    expect(header.style.top).toBe('0px');
    expect(header.style.minHeight).toBe(tokens.layout.headerHeight);
  });

  it('titles the document by the active view and scrolls to top on change (R17, R18)', () => {
    mockViewport(1440);
    stub();
    render(<App />);
    expect(document.title).toBe(`${MESSAGES.NAV_SUMMARY} · ${MESSAGES.APP_TITLE}`);
    expect(window.scrollTo).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: MESSAGES.NAV_RULES }));

    expect(document.title).toBe(`${MESSAGES.NAV_RULES} · ${MESSAGES.APP_TITLE}`);
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });

  it('titles the document with the app title when anonymous (R19)', () => {
    mockViewport(1440);
    stub({ status: 'anonymous' });
    render(<App />);
    expect(document.title).toBe(MESSAGES.APP_TITLE);
  });
});

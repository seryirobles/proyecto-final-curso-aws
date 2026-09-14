// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/useSession.js', () => ({ useSession: vi.fn() }));

import { useApp, VIEWS } from '../../src/hooks/useApp.js';
import { useSession } from '../../src/hooks/useSession.js';

function stubSession(session) {
  useSession.mockReturnValue({ session, login: vi.fn(), setPassword: vi.fn(), logout: vi.fn() });
}

describe('useApp', () => {
  beforeEach(() => stubSession({ status: 'loading' }));
  afterEach(() => vi.clearAllMocks());

  it('starts on the week view', () => {
    const { result } = renderHook(() => useApp());

    expect(result.current.activeView).toBe('week');
  });

  it('navigateTo switches activeView among all five nav targets (T43)', () => {
    const { result } = renderHook(() => useApp());
    const targets = ['library', 'rules', 'shoppingList', 'summary', 'week'];

    for (const target of targets) {
      act(() => result.current.navigateTo(target));
      expect(result.current.activeView).toBe(target);
    }
  });

  it('role Admin exposes no meal-planning nav target (R30)', () => {
    stubSession({ status: 'authenticated', role: 'Admin' });
    const { result } = renderHook(() => useApp());

    for (const view of VIEWS) {
      expect(result.current.navTargets).not.toContain(view);
    }
    expect(result.current.navTargets).toHaveLength(0);
  });

  it('role User exposes no admin nav target, and all five meal-planning targets (R31)', () => {
    stubSession({ status: 'authenticated', role: 'User' });
    const { result } = renderHook(() => useApp());

    expect(result.current.navTargets).not.toContain('admin');
    expect(result.current.navTargets).toEqual(VIEWS);
  });

  it('anonymous and passwordResetPending also expose no meal-planning nav target', () => {
    for (const session of [{ status: 'anonymous' }, { status: 'passwordResetPending' }]) {
      stubSession(session);
      const { result } = renderHook(() => useApp());
      expect(result.current.navTargets).toEqual([]);
    }
  });
});

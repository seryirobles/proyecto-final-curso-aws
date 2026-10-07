// @vitest-environment jsdom
// R46-R52: the active view mirrors the URL hash through the History API.
import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/hooks/useSession.js', () => ({ useSession: vi.fn() }));

import { useApp } from '../../src/hooks/useApp.js';
import { useSession } from '../../src/hooks/useSession.js';

const logout = vi.fn();

function stubSession(session) {
  useSession.mockReturnValue({ session, login: vi.fn(), setPassword: vi.fn(), logout });
}

const USER = { status: 'authenticated', role: 'User' };
let push;
let replace;

beforeEach(() => {
  window.history.replaceState(null, '', '/');
  logout.mockResolvedValue(undefined);
  push = vi.spyOn(window.history, 'pushState');
  replace = vi.spyOn(window.history, 'replaceState');
  stubSession(USER);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function pop(hash) {
  window.history.replaceState(null, '', hash);
  replace.mockClear();
  act(() => {
    window.dispatchEvent(new window.PopStateEvent('popstate'));
  });
}

describe('useApp URL hash', () => {
  it('pushes the new view hash for an authenticated User (R46)', () => {
    const { result } = renderHook(() => useApp());
    act(() => result.current.navigateTo('rules'));
    expect(push).toHaveBeenCalledTimes(1);
    expect(push).toHaveBeenCalledWith(null, '', '#/reglas');
    expect(result.current.activeView).toBe('rules');
  });

  it('does not push for the view already active (R47)', () => {
    const { result } = renderHook(() => useApp());
    act(() => result.current.navigateTo('summary'));
    expect(push).not.toHaveBeenCalled();
  });

  it('an explicit #/semana hash still opens the week view (R48)', () => {
    window.history.replaceState(null, '', '#/semana');
    const { result } = renderHook(() => useApp());
    expect(result.current.activeView).toBe('week');
  });

  it('starts on the view named by a known hash (R48)', () => {
    window.history.replaceState(null, '', '#/compra');
    const { result } = renderHook(() => useApp());
    expect(result.current.activeView).toBe('shoppingList');
  });

  it('popstate sets the view from the hash (R49)', () => {
    const { result } = renderHook(() => useApp());
    pop('#/resumen');
    expect(result.current.activeView).toBe('summary');
    expect(push).not.toHaveBeenCalled();
  });

  it('replaces an empty hash with #/resumen without pushing (R58)', () => {
    const { result } = renderHook(() => useApp());
    expect(result.current.activeView).toBe('summary');
    expect(replace).toHaveBeenCalledWith(null, '', '#/resumen');
    expect(push).not.toHaveBeenCalled();
  });

  it('popstate with an unknown hash falls back to summary and replaces it (R58)', () => {
    window.history.replaceState(null, '', '#/biblioteca');
    const { result } = renderHook(() => useApp());
    expect(result.current.activeView).toBe('library');
    pop('#/nope');
    expect(result.current.activeView).toBe('summary');
    expect(replace).toHaveBeenCalledWith(null, '', '#/resumen');
    expect(push).not.toHaveBeenCalled();
  });

  it.each([
    ['anonymous', { status: 'anonymous' }],
    ['loading', { status: 'loading' }],
    ['passwordResetPending', { status: 'passwordResetPending' }],
    ['Admin', { status: 'authenticated', role: 'Admin' }],
  ])('never writes the hash for a %s session (R51)', (_name, session) => {
    stubSession(session);
    const { result } = renderHook(() => useApp());
    act(() => result.current.navigateTo('rules'));
    pop('#/nope');
    expect(push).not.toHaveBeenCalled();
    expect(replace).not.toHaveBeenCalled();
    expect(window.location.hash).toBe('#/nope');
  });

  it('logout clears the hash without pushing (R52)', async () => {
    const { result } = renderHook(() => useApp());
    act(() => result.current.navigateTo('rules'));
    push.mockClear();
    replace.mockClear();
    await act(() => result.current.logout());
    expect(logout).toHaveBeenCalledTimes(1);
    expect(replace).toHaveBeenCalledWith(null, '', '/');
    expect(window.location.hash).toBe('');
    expect(push).not.toHaveBeenCalled();
  });

  it('logout resets the view to summary (R59)', async () => {
    const { result } = renderHook(() => useApp());
    act(() => result.current.navigateTo('rules'));
    await act(() => result.current.logout());
    expect(result.current.activeView).toBe('summary');
  });

  it('re-login after logout starts on summary (R59)', async () => {
    const { result, rerender } = renderHook(() => useApp());
    act(() => result.current.navigateTo('rules'));
    await act(() => result.current.logout());
    stubSession({ status: 'anonymous' });
    rerender();
    stubSession(USER);
    rerender();
    expect(result.current.activeView).toBe('summary');
    expect(window.location.hash).toBe('#/resumen');
  });
});

// @vitest-environment jsdom
// R18, R19: document.title follows the session and the active view.

import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useDocumentTitle } from '../../src/hooks/useDocumentTitle.js';
import { MESSAGES } from '../../src/messages/index.js';

describe('useDocumentTitle', () => {
  it('sets "<view label> · <app title>" for a User', () => {
    renderHook(() => useDocumentTitle(MESSAGES.NAV_WEEK));
    expect(document.title).toBe('Semana · Planificador semanal');
  });

  it('follows the label as the view changes', () => {
    const { rerender } = renderHook(({ label }) => useDocumentTitle(label), {
      initialProps: { label: MESSAGES.NAV_WEEK },
    });
    rerender({ label: MESSAGES.NAV_RULES });
    expect(document.title).toBe('Reglas · Planificador semanal');
  });

  it('is the bare application title with no label', () => {
    renderHook(() => useDocumentTitle(null));
    expect(document.title).toBe(MESSAGES.APP_TITLE);
  });
});

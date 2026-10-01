// @vitest-environment jsdom
// R34, R39, R41, R43: the shared Banner's roles, prefix, edge and empty case.
import { afterEach, describe, expect, it } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { Banner } from '../../src/components/Banner.jsx';
import { MESSAGES } from '../../src/messages/index.js';
import { tokens } from '../../src/tokens/index.js';

afterEach(cleanup);

describe('Banner', () => {
  it('renders an error as role=alert with the catalogue prefix and a honey 4px edge (R34, R41)', () => {
    render(<Banner>Algo falló.</Banner>);

    const alert = screen.getByRole('alert');
    expect(alert.textContent).toContain(MESSAGES.ERROR_PREFIX);
    expect(alert.textContent).toContain('Algo falló.');
    const probe = document.createElement('div');
    probe.style.borderLeft = `4px solid ${tokens.color.honey}`;
    probe.style.color = tokens.color.ink;
    probe.style.backgroundColor = tokens.color.honeySoft;
    expect(alert.style.borderLeft).toBe(probe.style.borderLeft);
    expect(alert.style.color).toBe(probe.style.color);
    expect(alert.style.backgroundColor).toBe(probe.style.backgroundColor);
  });

  it('renders a result as role=status without the error prefix (R39)', () => {
    render(<Banner tone="result">Guardado.</Banner>);

    const status = screen.getByRole('status');
    expect(status.textContent).toBe('Guardado.');
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('renders nothing without children (R43)', () => {
    const { container } = render(<Banner>{null}</Banner>);

    expect(container.innerHTML).toBe('');
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.queryByRole('status')).toBeNull();
  });
});

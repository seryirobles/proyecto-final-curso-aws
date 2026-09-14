// @vitest-environment jsdom
// T51 (R24, R29): renders username + password + submit, an inline error, and
// crucially no registration control anywhere on the screen.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { LoginView } from '../../src/components/LoginView.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

function baseProps(overrides = {}) {
  return {
    username: '',
    setUsername: vi.fn(),
    password: '',
    setPassword: vi.fn(),
    canSubmit: true,
    submit: vi.fn(),
    error: null,
    isSubmitting: false,
    ...overrides,
  };
}

describe('LoginView', () => {
  it('renders a username field, a password field and a submit control (R24)', () => {
    render(<LoginView {...baseProps()} />);

    expect(screen.getByText(MESSAGES.LOGIN_USERNAME_LABEL)).not.toBeNull();
    expect(screen.getByText(MESSAGES.LOGIN_PASSWORD_LABEL)).not.toBeNull();
    expect(screen.getByText(MESSAGES.LOGIN_SUBMIT)).not.toBeNull();
  });

  it('masks the password field (security-relevant: type="password")', () => {
    render(<LoginView {...baseProps()} />);

    expect(screen.getByLabelText(MESSAGES.LOGIN_PASSWORD_LABEL).type).toBe('password');
  });

  it('renders the caught error detail inline', () => {
    render(<LoginView {...baseProps({ error: 'Usuario o contraseña incorrectos.' })} />);

    expect(screen.getByText('Usuario o contraseña incorrectos.')).not.toBeNull();
  });

  it('offers no registration control anywhere on the screen (R29)', () => {
    render(<LoginView {...baseProps()} />);

    const registrationPattern = /registr|crear cuenta|sign\s*up/i;
    document.querySelectorAll('button, a').forEach((el) => {
      expect(el.textContent).not.toMatch(registrationPattern);
    });
  });
});

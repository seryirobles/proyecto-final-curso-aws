// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { ConnectionLostBanner } from '../../src/components/ConnectionLostBanner.jsx';
import { MESSAGES } from '../../src/messages/index.js';

afterEach(cleanup);

describe('ConnectionLostBanner', () => {
  it('renders nothing when connectionLost is false', () => {
    const { container } = render(<ConnectionLostBanner connectionLost={false} />);

    expect(container.firstChild).toBeNull();
  });

  it('renders MESSAGES.CONNECTION_LOST when connectionLost is true (FR-RT-03)', () => {
    render(<ConnectionLostBanner connectionLost={true} />);

    expect(screen.getByText(MESSAGES.CONNECTION_LOST)).not.toBeNull();
  });
});

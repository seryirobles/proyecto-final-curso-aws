// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WeekLabel } from '../../src/components/WeekLabel.jsx';
import { formatDate } from '../../src/locale.js';
import { MESSAGES } from '../../src/messages/index.js';

describe('WeekLabel', () => {
  // Two-tier hierarchy (T75, design.md section 10.6): designation and date
  // range are now separate text nodes, not one joined string.
  it('renders the current designation and the date range via formatDate', () => {
    render(<WeekLabel designation="current" monday="2026-08-10" sunday="2026-08-16" />);

    expect(screen.getByText(MESSAGES.WEEK_LABEL_CURRENT)).not.toBeNull();
    const expectedRange = `${formatDate(new Date('2026-08-10'))}–${formatDate(new Date('2026-08-16'))}`;
    expect(screen.getByText(expectedRange)).not.toBeNull();
  });

  it('renders the next designation and the date range via formatDate', () => {
    render(<WeekLabel designation="next" monday="2026-08-17" sunday="2026-08-23" />);

    expect(screen.getByText(MESSAGES.WEEK_LABEL_NEXT)).not.toBeNull();
    const expectedRange = `${formatDate(new Date('2026-08-17'))}–${formatDate(new Date('2026-08-23'))}`;
    expect(screen.getByText(expectedRange)).not.toBeNull();
  });
});

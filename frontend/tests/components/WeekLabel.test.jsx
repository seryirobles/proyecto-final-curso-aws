// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WeekLabel } from '../../src/components/WeekLabel.jsx';
import { formatDate } from '../../src/locale.js';
import { MESSAGES } from '../../src/messages/index.js';

describe('WeekLabel', () => {
  it('renders the current designation and the date range via formatDate', () => {
    render(<WeekLabel designation="current" monday="2026-08-10" sunday="2026-08-16" />);

    const expected = `${MESSAGES.WEEK_LABEL_CURRENT} · ${formatDate(new Date('2026-08-10'))}–${formatDate(new Date('2026-08-16'))}`;
    expect(screen.getByText(expected)).not.toBeNull();
  });

  it('renders the next designation', () => {
    render(<WeekLabel designation="next" monday="2026-08-17" sunday="2026-08-23" />);

    const expected = `${MESSAGES.WEEK_LABEL_NEXT} · ${formatDate(new Date('2026-08-17'))}–${formatDate(new Date('2026-08-23'))}`;
    expect(screen.getByText(expected)).not.toBeNull();
  });
});

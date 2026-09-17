// Week designation + Monday-Sunday date range, reused by every week-scoped
// view (R16, R21; design.md section 5). Dates format through
// `locale.js:formatDate`, never a hand-built string.

import { tokens } from '../tokens/index.js';
import { formatDate } from '../locale.js';
import { MESSAGES } from '../messages/index.js';

export function WeekLabel({ designation, monday, sunday }) {
  const designationLabel =
    designation === 'next' ? MESSAGES.WEEK_LABEL_NEXT : MESSAGES.WEEK_LABEL_CURRENT;
  const rangeLabel = `${formatDate(new Date(monday))}–${formatDate(new Date(sunday))}`;

  return (
    <span style={{ display: 'flex', flexDirection: 'column' }}>
      <span style={{ fontFamily: tokens.fontFamily.heading, color: tokens.color.ink }}>
        {designationLabel}
      </span>
      <span style={{ fontFamily: tokens.fontFamily.label, color: tokens.color.ink2 }}>
        {rangeLabel}
      </span>
    </span>
  );
}

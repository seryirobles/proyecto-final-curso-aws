// Shared message banner (frontend_ux_phase1 R34-R43): ink on honeySoft with a
// honey edge, so meaning is not colour-only. Text always comes from the catalogue.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

const bannerStyle = {
  fontFamily: tokens.fontFamily.body,
  backgroundColor: tokens.color.honeySoft,
  color: tokens.color.ink,
  borderLeft: `4px solid ${tokens.color.honey}`,
  borderRadius: tokens.radius.sm,
  padding: tokens.space.md,
  margin: `${tokens.space.sm} ${tokens.space.none}`,
};

export function Banner({ tone = 'error', children }) {
  if (!children) return null;

  if (tone === 'error') {
    return (
      <div role="alert" style={bannerStyle}>
        <strong>{MESSAGES.ERROR_PREFIX} </strong>
        {children}
      </div>
    );
  }

  return (
    <div role="status" style={bannerStyle}>
      {children}
    </div>
  );
}

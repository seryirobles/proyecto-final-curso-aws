// FR-RT-03 connection-loss indicator (feature 26, done); wiring it is this
// feature's job (design.md section 1.2). Pure - `connectionLost` comes off
// whichever poll the active view holds (App.jsx picks it).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

export function ConnectionLostBanner({ connectionLost }) {
  if (!connectionLost) return null;

  return (
    <p
      style={{
        backgroundColor: tokens.color.honeySoft,
        color: tokens.color.ink,
        padding: tokens.space.md,
        margin: tokens.space.none,
      }}
    >
      {MESSAGES.CONNECTION_LOST}
    </p>
  );
}

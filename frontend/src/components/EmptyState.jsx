// Defined empty state with guidance (R19, docs/conventions.md "UI
// obligations"). `message` is sourced from MESSAGES by the calling view -
// this component only renders what it is given.

import { tokens } from '../tokens/index.js';

export function EmptyState({ message }) {
  return (
    <p
      style={{
        fontFamily: tokens.fontFamily.body,
        color: tokens.color.ink2,
        padding: tokens.space.md,
        border: `1px dashed ${tokens.color.line}`,
        borderRadius: tokens.radius.md,
        textAlign: 'center',
      }}
    >
      {message}
    </p>
  );
}

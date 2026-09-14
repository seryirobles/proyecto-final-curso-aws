// Defined loading state (R20, docs/conventions.md "UI obligations"). A
// default message keeps every view's slow operation covered without
// re-deriving the same text per call site.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';

export function LoadingState({ message = MESSAGES.LOADING_STATE_DEFAULT }) {
  return <p style={{ color: tokens.color.ink2, padding: tokens.space.md }}>{message}</p>;
}

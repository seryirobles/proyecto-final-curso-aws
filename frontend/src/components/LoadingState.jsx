// Defined loading state (R20, docs/conventions.md "UI obligations"). A
// default message keeps every view's slow operation covered without
// re-deriving the same text per call site.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { useLoadingShimmer } from '../hooks/useLoadingShimmer.js';

export function LoadingState({ message = MESSAGES.LOADING_STATE_DEFAULT }) {
  const pulse = useLoadingShimmer();

  return (
    <div style={{ fontFamily: tokens.fontFamily.body, padding: tokens.space.md }}>
      <div
        data-testid="loading-shimmer"
        style={{
          height: '4px',
          borderRadius: tokens.radius.pill,
          marginBottom: tokens.space.sm,
          backgroundColor: pulse ? tokens.color.surface2 : tokens.color.surface,
        }}
      />
      <p style={{ margin: tokens.space.none, color: tokens.color.ink2 }}>{message}</p>
    </div>
  );
}

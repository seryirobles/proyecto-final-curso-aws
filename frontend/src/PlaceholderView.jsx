import { tokens } from './tokens/index.js';
import { MESSAGES } from './messages/index.js';

/**
 * The single placeholder component required by the scaffold (feature 1,
 * project_scaffold). NOT a product screen: it exists only to prove the
 * toolchain — bundler, styling tokens and the messages module — works end to
 * end. Product screens are feature 20 (frontend_spa).
 */
export function PlaceholderView() {
  return (
    <main
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.space.md,
        padding: tokens.space.lg,
        color: tokens.color.ink,
        backgroundColor: tokens.color.paper,
      }}
    >
      <h1 style={{ fontSize: tokens.fontSize.xl, margin: tokens.space.none }}>
        {MESSAGES.SCAFFOLD_PLACEHOLDER_TITLE}
      </h1>
      <p
        style={{
          fontSize: tokens.fontSize.md,
          margin: tokens.space.none,
          color: tokens.color.ink2,
        }}
      >
        {MESSAGES.SCAFFOLD_PLACEHOLDER_BODY}
      </p>
    </main>
  );
}

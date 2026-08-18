import { MESSAGES } from '../src/messages/index.js';

/**
 * Substitutes the `%APP_TITLE%` placeholder in index.html with the Castilian
 * Spanish string from the messages module. The browser tab title is
 * user-facing UI (FR-UX-01, FR-UX-03) and must not hardcode a Spanish
 * literal outside src/messages/. Works for both `vite build` and the dev
 * server — `transformIndexHtml` runs in both.
 */
export function htmlMessages() {
  return {
    name: 'html-messages',
    transformIndexHtml(html) {
      // Replacement is a callback, not a string: String.replace interprets
      // `$&`, `$'`, `` $` ``, `$$` and `$<name>` as special patterns when the
      // replacement is a string, which would silently mangle any message
      // value containing `$`. A callback's return value is used literally.
      return html.replace('%APP_TITLE%', () => MESSAGES.APP_TITLE);
    },
  };
}

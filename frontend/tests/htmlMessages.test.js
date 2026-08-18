import { describe, expect, it } from 'vitest';
import { htmlMessages } from '../vite-plugins/htmlMessages.js';
import { MESSAGES } from '../src/messages/index.js';

describe('htmlMessages', () => {
  it('resolves the %APP_TITLE% placeholder to the es-ES messages module value', () => {
    const plugin = htmlMessages();
    const input = '<html><head><title>%APP_TITLE%</title></head></html>';

    const output = plugin.transformIndexHtml(input);

    expect(output).toContain(`<title>${MESSAGES.APP_TITLE}</title>`);
    expect(output).not.toContain('%APP_TITLE%');
  });

  it('substitutes a message value containing `$&` literally, without expanding it', () => {
    // `String.replace(pattern, replacementString)` treats `$&` as "the
    // matched substring" when the replacement is a string, which would
    // duplicate the placeholder instead of inserting it literally. Using a
    // callback replacement (as htmlMessages does) must avoid that expansion.
    const originalTitle = MESSAGES.APP_TITLE;
    MESSAGES.APP_TITLE = "Precio: $& / $' descuento";

    try {
      const plugin = htmlMessages();
      const input = '<html><head><title>%APP_TITLE%</title></head></html>';

      const output = plugin.transformIndexHtml(input);

      expect(output).toContain(`<title>${MESSAGES.APP_TITLE}</title>`);
      expect(output).not.toContain('%APP_TITLE%');
    } finally {
      MESSAGES.APP_TITLE = originalTitle;
    }
  });
});

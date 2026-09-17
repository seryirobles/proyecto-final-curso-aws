import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { loadSelfHostedFonts } from '../src/fonts.js';

describe('loadSelfHostedFonts', () => {
  let originalFontFace;
  let originalDocument;

  beforeEach(() => {
    originalFontFace = globalThis.FontFace;
    originalDocument = globalThis.document;
  });

  afterEach(() => {
    globalThis.FontFace = originalFontFace;
    globalThis.document = originalDocument;
  });

  it('registers exactly the five expected (family, weight) faces', async () => {
    const registered = [];
    const added = [];

    class FakeFontFace {
      constructor(family, source, { weight }) {
        registered.push([family, weight]);
      }
      load() {
        return Promise.resolve(this);
      }
    }
    globalThis.FontFace = FakeFontFace;
    globalThis.document = { fonts: { add: (face) => added.push(face) } };

    loadSelfHostedFonts();
    // Flush the .load().then(...) microtask queued per face.
    await Promise.resolve();
    await Promise.resolve();

    expect(registered).toEqual([
      ['Baloo 2', '600'],
      ['Baloo 2', '700'],
      ['Nunito', '400'],
      ['Nunito', '600'],
      ['DM Mono', '400'],
    ]);
    expect(added).toHaveLength(5);
  });

  it('swallows a rejected load() without an unhandled rejection', async () => {
    class RejectingFontFace {
      load() {
        return Promise.reject(new Error('network failure'));
      }
    }
    globalThis.FontFace = RejectingFontFace;
    globalThis.document = { fonts: { add: () => {} } };

    const unhandled = [];
    const onUnhandledRejection = (reason) => unhandled.push(reason);
    globalThis.process.on('unhandledRejection', onUnhandledRejection);

    try {
      expect(() => loadSelfHostedFonts()).not.toThrow();
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    } finally {
      globalThis.process.off('unhandledRejection', onUnhandledRejection);
    }

    expect(unhandled).toHaveLength(0);
  });
});

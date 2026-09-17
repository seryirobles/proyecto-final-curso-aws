/**
 * Self-hosted font loading via the CSS Font Loading API (design.md section
 * 10.1) - not `@font-face`, not a stylesheet, not a CDN `<link>`. The 5
 * `.woff2` files are Google Fonts' own OFL-licensed static files, fetched
 * once at build/asset time under frontend/src/assets/fonts/.
 */

const FACES = [
  ['Baloo 2', new URL('./assets/fonts/baloo2-600.woff2', import.meta.url), '600'],
  ['Baloo 2', new URL('./assets/fonts/baloo2-700.woff2', import.meta.url), '700'],
  ['Nunito', new URL('./assets/fonts/nunito-400.woff2', import.meta.url), '400'],
  ['Nunito', new URL('./assets/fonts/nunito-600.woff2', import.meta.url), '600'],
  ['DM Mono', new URL('./assets/fonts/dmmono-400.woff2', import.meta.url), '400'],
];

export function loadSelfHostedFonts() {
  FACES.forEach(([family, url, weight]) => {
    const face = new FontFace(family, `url(${url})`, { weight });
    face
      .load()
      .then((loaded) => document.fonts.add(loaded))
      .catch(() => {
        // fontFamily.js's fallback stack already covers a failed load (design.md 10.1) -
        // a network/format failure here is not a user-facing error.
      });
  });
}

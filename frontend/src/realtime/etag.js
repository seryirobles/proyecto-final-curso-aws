// Marker quoting/parsing for the `ETag`/`If-None-Match` wire format
// (docs/rest_api_contract.md section 6). Pure — no DOM, no fetch.

const SINGLE_QUOTED_DIGITS = /^"(\d+)"$/;

export function quoteMarker(marker) {
  return `"${marker}"`;
}

export function parseMarker(headerValue) {
  if (typeof headerValue !== 'string') return null;
  const match = SINGLE_QUOTED_DIGITS.exec(headerValue.trim());
  return match ? Number(match[1]) : null;
}

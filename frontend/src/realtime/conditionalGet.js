// The default `fetchResource` transport: wraps `fetch` with `If-None-Match` /
// `ETag` (docs/rest_api_contract.md section 6). Testable by stubbing
// `globalThis.fetch` - no DOM needed.

import { parseMarker, quoteMarker } from './etag.js';

export function conditionalGet(url) {
  return async function fetchResource(heldMarker) {
    const headers = heldMarker == null ? {} : { 'If-None-Match': quoteMarker(heldMarker) };
    const response = await fetch(url, { headers });
    if (response.status === 304) {
      return { status: 304, marker: heldMarker, body: null }; // R13
    }
    return {
      status: 200,
      marker: parseMarker(response.headers.get('ETag')),
      body: await response.json(),
    }; // R14
  };
}

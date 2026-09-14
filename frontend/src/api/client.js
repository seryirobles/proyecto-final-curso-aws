// The one fetch boundary (design.md section 4.1): every view hook's mutation
// or read goes through `apiFetch`, never `fetch` directly. Auth is the
// `HttpOnly` cookie alone - no token is ever read or set here.

import { MESSAGES } from '../messages/index.js';

/**
 * `detail` is already es-ES, copied verbatim from `planner_core.messages`
 * (rest_api_contract.md section 4) - never composed here (R15).
 */
export class ApiError extends Error {
  constructor({ status, code, detail, details }) {
    super(detail);
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.details = details;
  }
}

export async function apiFetch(path, { method = 'GET', body, signal, onHeaders } = {}) {
  let response;
  try {
    response = await fetch(path, {
      method,
      credentials: 'include',
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    // A rejected fetch is a connectivity failure, not a server response -
    // no `problem+json` body exists to read (design.md section 4.1).
    throw new ApiError({ status: 0, code: 'NETWORK_ERROR', detail: MESSAGES.GENERIC_ERROR });
  }

  if (response.status === 204) {
    onHeaders?.(response.headers);
    return null;
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError({
      status: response.status,
      code: payload?.code ?? 'UNKNOWN_ERROR',
      detail: payload?.detail ?? MESSAGES.GENERIC_ERROR,
      details: payload?.details,
    });
  }
  // Optional: reads the response's ETag for a mutation's optimistic
  // self-update (design.md section 4.2) - additive, no existing caller passes it.
  onHeaders?.(response.headers);
  return payload;
}

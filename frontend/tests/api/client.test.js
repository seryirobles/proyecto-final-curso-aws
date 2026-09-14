import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiFetch } from '../../src/api/client.js';
import { MESSAGES } from '../../src/messages/index.js';

function jsonResponse(status, body) {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: () => Promise.resolve(body),
  };
}

describe('apiFetch', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('passes a 200 response through as the parsed payload', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(200, { weekId: '2026-W34' }));

    const result = await apiFetch('/v1/weeks/2026-W34');

    expect(result).toEqual({ weekId: '2026-W34' });
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/v1/weeks/2026-W34',
      expect.objectContaining({ method: 'GET', credentials: 'include' }),
    );
  });

  it('passes a 204 response through as null', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue({ status: 204, ok: true, json: () => Promise.resolve(null) });

    const result = await apiFetch('/v1/library/recipes/01J8', { method: 'DELETE' });

    expect(result).toBeNull();
  });

  it('throws an ApiError with the problem+json fields on a non-2xx response', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse(409, {
        type: 'urn:planner:pin-rules-affected',
        title: 'Pin rules affected',
        status: 409,
        detail: 'Hay reglas que fijan esta receta.',
        code: 'PIN_RULES_AFFECTED',
        details: { pins: [{ day: 7, slot: 1 }] },
      }),
    );

    await expect(apiFetch('/v1/library/recipes/01J8', { method: 'DELETE' })).rejects.toMatchObject({
      status: 409,
      code: 'PIN_RULES_AFFECTED',
      detail: 'Hay reglas que fijan esta receta.',
      details: { pins: [{ day: 7, slot: 1 }] },
    });
  });

  it('throws an ApiError instance, not just a matching shape', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(500, { code: 'UNKNOWN_ERROR' }));

    await expect(apiFetch('/v1/rules')).rejects.toBeInstanceOf(ApiError);
  });

  it('passes the response headers to onHeaders on both a 200 and a 204', async () => {
    const headers200 = new Headers({ ETag: '"19"' });
    globalThis.fetch = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      headers: headers200,
      json: () => Promise.resolve({}),
    });
    const onHeaders200 = vi.fn();
    await apiFetch('/v1/weeks/2026-W34/days/1/slots/1/definitive', {
      method: 'PUT',
      body: { candidateId: 'c1' },
      onHeaders: onHeaders200,
    });
    expect(onHeaders200.mock.calls[0][0].get('ETag')).toBe('"19"');

    const headers204 = new Headers({ ETag: '"20"' });
    globalThis.fetch = vi.fn().mockResolvedValue({ status: 204, ok: true, headers: headers204 });
    const onHeaders204 = vi.fn();
    await apiFetch('/v1/weeks/2026-W34/days/1/slots/1/definitive', {
      method: 'DELETE',
      onHeaders: onHeaders204,
    });
    expect(onHeaders204.mock.calls[0][0].get('ETag')).toBe('"20"');
  });

  it('throws code NETWORK_ERROR when fetch itself rejects', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(apiFetch('/v1/rules')).rejects.toMatchObject({
      code: 'NETWORK_ERROR',
      detail: MESSAGES.GENERIC_ERROR,
    });
  });
});

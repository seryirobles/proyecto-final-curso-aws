import { afterEach, describe, expect, it, vi } from 'vitest';
import { conditionalGet } from '../../src/realtime/conditionalGet.js';

describe('conditionalGet', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('maps a 304 response to the held marker with no body', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ status: 304, headers: new Map() });
    vi.stubGlobal('fetch', fetchMock);

    const result = await conditionalGet('/v1/shopping-list')(7);

    expect(result).toEqual({ status: 304, marker: 7, body: null });
    expect(fetchMock).toHaveBeenCalledWith(
      '/v1/shopping-list',
      expect.objectContaining({ headers: { 'If-None-Match': '"7"' } }),
    );
  });

  it('maps a 200 response to the parsed ETag marker and JSON body', async () => {
    const headers = new Map([['ETag', '"8"']]);
    const fetchMock = vi.fn().mockResolvedValue({
      status: 200,
      headers: { get: (name) => headers.get(name) ?? null },
      json: () => Promise.resolve({ items: [] }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await conditionalGet('/v1/shopping-list')(7);

    expect(result).toEqual({ status: 200, marker: 8, body: { items: [] } });
  });

  it('omits the header when no marker is held yet', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      status: 200,
      headers: { get: () => '"1"' },
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal('fetch', fetchMock);

    await conditionalGet('/v1/shopping-list')(null);

    expect(fetchMock).toHaveBeenCalledWith('/v1/shopping-list', { headers: {} });
  });
});

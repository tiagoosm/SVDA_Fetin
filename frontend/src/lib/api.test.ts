import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, request, setUnauthorizedHandler } from './api';

function stubFetch(status: number, body: unknown) {
  const mock = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal('fetch', mock);
  return mock;
}

afterEach(() => setUnauthorizedHandler(null));

describe('request', () => {
  it('sends the session cookie and a JSON body', async () => {
    const mock = stubFetch(200, { ok: true });
    await request('/auth/login', { method: 'POST', body: { email: 'a@b.co' } });
    expect(mock).toHaveBeenCalledWith(
      '/api/auth/login',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'a@b.co' }),
      }),
    );
  });

  it('returns the parsed response', async () => {
    stubFetch(200, { conversations: [] });
    await expect(request('/conversations')).resolves.toEqual({ conversations: [] });
  });

  it('turns an error response into an ApiError with the server message', async () => {
    stubFetch(400, { error: 'E-mail inválido' });
    await expect(request('/auth/register')).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      message: 'E-mail inválido',
    });
  });

  it('uses a generic message when the error body is not JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('<html>', { status: 500 })),
    );
    await expect(request('/conversations')).rejects.toThrow('Algo deu errado');
  });

  it('reports a network failure as status 0', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))),
    );
    const error = await request('/conversations').catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 0 });
  });

  it('notifies when an authenticated request is unauthorized', async () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    stubFetch(401, { error: 'Usuário não autenticado' });
    await expect(request('/conversations')).rejects.toBeInstanceOf(ApiError);
    expect(handler).toHaveBeenCalledOnce();
  });

  it('does not treat a failed login as an expired session', async () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    stubFetch(401, { error: 'E-mail ou senha incorretos' });
    await expect(request('/auth/login', { method: 'POST', body: {} })).rejects.toBeInstanceOf(
      ApiError,
    );
    expect(handler).not.toHaveBeenCalled();
  });
});

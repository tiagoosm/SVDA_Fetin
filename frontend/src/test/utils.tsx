import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { vi } from 'vitest';
import { App } from '@/App';
import { AuthProvider } from '@/context/AuthProvider';
import type { User } from '@/types/api';

export const USER: User = {
  id: 1,
  email: 'ana@example.com',
  name: 'Ana',
  herd_size: 'small',
  cattle_type: 'dairy',
};

interface ApiRequest {
  path: string;
  method: string;
  body: Record<string, unknown> | undefined;
}

interface ApiResponse {
  status?: number;
  body?: unknown;
}

type Handler = (request: ApiRequest) => ApiResponse | Promise<ApiResponse>;
type Route = [method: string, path: string | RegExp, handler: Handler];

/** Replaces fetch with an in-memory fake API. Unmatched requests fail the test loudly. */
export function mockApi(routes: Route[]) {
  const calls: ApiRequest[] = [];

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input).replace(/^\/api/, '');
    const method = init?.method ?? 'GET';
    const body = init?.body
      ? (JSON.parse(String(init.body)) as Record<string, unknown>)
      : undefined;
    const request = { path, method, body };
    calls.push(request);

    const route = routes.find(
      ([routeMethod, pattern]) =>
        routeMethod === method &&
        (typeof pattern === 'string' ? pattern === path : pattern.test(path)),
    );
    if (!route) {
      return new Response(JSON.stringify({ error: `Unmocked request: ${method} ${path}` }), {
        status: 500,
      });
    }
    const { status = 200, body: responseBody = {} } = await route[2](request);
    return new Response(JSON.stringify(responseBody), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  });

  vi.stubGlobal('fetch', fetchMock);
  return { calls, fetchMock };
}

export function renderApp(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

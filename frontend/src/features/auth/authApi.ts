import { request } from '@/lib/api';
import type { PublicConfig, RegisterPayload, User } from '@/types/api';

export const authApi = {
  me: () => request<User>('/auth/me'),
  login: (email: string, password: string) =>
    request<{ message: string }>('/auth/login', { method: 'POST', body: { email, password } }),
  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),
  register: (payload: RegisterPayload) =>
    request<{ message: string }>('/auth/register', { method: 'POST', body: payload }),
  publicConfig: () => request<PublicConfig>('/config'),
};

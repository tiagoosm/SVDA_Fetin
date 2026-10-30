import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { authApi } from '@/features/auth/authApi';
import { setUnauthorizedHandler } from '@/lib/api';
import type { User } from '@/types/api';
import { AuthContext } from './auth-context';
import type { AuthState, AuthStatus } from './auth-context';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  // Restore the session (the cookie is HttpOnly, so the only way to know is to ask).
  useEffect(() => {
    let active = true;
    authApi
      .me()
      .then((me) => {
        if (!active) return;
        setUser(me);
        setStatus('authenticated');
      })
      .catch(() => {
        if (active) setStatus('anonymous');
      });
    return () => {
      active = false;
    };
  }, []);

  // An authenticated request failing with 401 means the session expired.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
      setStatus('anonymous');
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    await authApi.login(email, password);
    setUser(await authApi.me());
    setStatus('authenticated');
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      setStatus('anonymous');
    }
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, status, login, logout }),
    [user, status, login, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

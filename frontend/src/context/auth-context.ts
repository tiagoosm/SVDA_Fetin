import { createContext, useContext } from 'react';
import type { User } from '@/types/api';

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous';

export interface AuthState {
  user: User | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside <AuthProvider>');
  return value;
}

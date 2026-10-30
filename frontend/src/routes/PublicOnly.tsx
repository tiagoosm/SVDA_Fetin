import { Navigate, Outlet } from 'react-router';
import { useAuth } from '@/context/auth-context';
import { LoadingScreen } from '@/components/LoadingScreen';

/** Login and sign-up are for visitors; signed-in users go straight to their conversations. */
export function PublicOnly() {
  const { status } = useAuth();

  if (status === 'loading') return <LoadingScreen />;
  if (status === 'authenticated') return <Navigate to="/conversations" replace />;
  return <Outlet />;
}

import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from '@/context/auth-context';
import { LoadingScreen } from '@/components/LoadingScreen';

/** Renders the nested routes only for signed-in users. */
export function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'loading') return <LoadingScreen />;
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location }} />;
  return <Outlet />;
}

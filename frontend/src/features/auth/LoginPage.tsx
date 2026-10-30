import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { TextField } from '@/components/ui/Field';
import { useAuth } from '@/context/auth-context';
import { ApiError } from '@/lib/api';
import { AuthLayout } from './AuthLayout';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const justRegistered = (location.state as { registered?: boolean } | null)?.registered === true;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      navigate('/conversations', { replace: true });
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : 'Não foi possível entrar. Tente novamente.',
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Entrar">
      <form onSubmit={handleSubmit} className="grid gap-4" noValidate>
        {justRegistered ? <Alert tone="info">Conta criada. Entre para continuar.</Alert> : null}
        <TextField
          label="E-mail"
          type="email"
          autoComplete="email"
          inputMode="email"
          placeholder="voce@exemplo.com"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <TextField
          label="Senha"
          type="password"
          autoComplete="current-password"
          placeholder="Sua senha"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {error ? <Alert tone="error">{error}</Alert> : null}
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Entrando…' : 'Entrar'}
        </Button>
        <p className="flex items-center gap-3 text-sm text-muted before:h-px before:flex-1 before:bg-current/30 after:h-px after:flex-1 after:bg-current/30">
          ou
        </p>
        <Link
          to="/register"
          className="inline-flex min-h-13 w-full items-center justify-center rounded-full text-lg font-bold text-moss ring-2 ring-moss ring-inset transition-colors hover:bg-moss/5"
        >
          Criar conta
        </Link>
      </form>
    </AuthLayout>
  );
}

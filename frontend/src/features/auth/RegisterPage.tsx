import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { SelectField, TextField } from '@/components/ui/Field';
import { ApiError } from '@/lib/api';
import { CATTLE_TYPE_LABELS, HERD_SIZE_LABELS } from '@/lib/labels';
import type { CattleType, HerdSize } from '@/types/api';
import { AuthLayout } from './AuthLayout';
import { authApi } from './authApi';

const HERD_SIZE_OPTIONS = Object.entries(HERD_SIZE_LABELS).map(([value, label]) => ({
  value,
  label,
}));
const CATTLE_TYPE_OPTIONS = Object.entries(CATTLE_TYPE_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export function RegisterPage() {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [herdSize, setHerdSize] = useState('');
  const [cattleType, setCattleType] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [inviteRequired, setInviteRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // The invite field only exists for public demos that set INVITE_CODE on the server.
  useEffect(() => {
    let active = true;
    authApi
      .publicConfig()
      .then((config) => {
        if (active) setInviteRequired(config.invite_required);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await authApi.register({
        name: name.trim(),
        email: email.trim(),
        password,
        herd_size: herdSize as HerdSize,
        cattle_type: cattleType as CattleType,
        ...(inviteRequired ? { invite_code: inviteCode.trim() } : {}),
      });
      navigate('/login', { replace: true, state: { registered: true } });
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Não foi possível criar a conta. Tente novamente.',
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Criar conta" compact>
      <form onSubmit={handleSubmit} className="grid gap-4">
        <TextField
          label="Nome completo"
          autoComplete="name"
          required
          maxLength={100}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <TextField
          label="E-mail"
          type="email"
          autoComplete="email"
          inputMode="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <TextField
          label="Senha"
          hint="(mínimo de 8 caracteres)"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={128}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField
            label="Tipo de gado"
            placeholder="Escolha"
            options={CATTLE_TYPE_OPTIONS}
            required
            value={cattleType}
            onChange={(event) => setCattleType(event.target.value)}
          />
          <SelectField
            label="Tamanho do rebanho"
            placeholder="Escolha"
            options={HERD_SIZE_OPTIONS}
            required
            value={herdSize}
            onChange={(event) => setHerdSize(event.target.value)}
          />
        </div>
        {inviteRequired ? (
          <TextField
            label="Código de convite"
            autoComplete="off"
            required
            maxLength={100}
            value={inviteCode}
            onChange={(event) => setInviteCode(event.target.value)}
          />
        ) : null}
        {error ? <Alert tone="error">{error}</Alert> : null}
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Criando conta…' : 'Criar conta'}
        </Button>
        <p className="text-center text-sm text-muted">
          Já tem conta?{' '}
          <Link to="/login" className="font-semibold text-moss underline underline-offset-2">
            Entrar
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}

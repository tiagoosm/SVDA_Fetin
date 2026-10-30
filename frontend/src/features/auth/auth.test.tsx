import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { mockApi, renderApp, USER } from '@/test/utils';

const UNAUTHENTICATED = { status: 401, body: { error: 'Usuário não autenticado' } };

describe('login', () => {
  it('sends anonymous visitors from the app to the login page', async () => {
    mockApi([['GET', '/auth/me', () => UNAUTHENTICATED]]);
    renderApp('/conversations');
    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument();
  });

  it('signs in and opens the conversations', async () => {
    let signedIn = false;
    const { calls } = mockApi([
      ['GET', '/auth/me', () => (signedIn ? { body: USER } : UNAUTHENTICATED)],
      [
        'POST',
        '/auth/login',
        () => {
          signedIn = true;
          return { body: { message: 'ok' } };
        },
      ],
      ['GET', '/conversations', () => ({ body: { conversations: [] } })],
    ]);
    const user = userEvent.setup();
    renderApp('/login');

    await user.type(await screen.findByLabelText('E-mail'), ' ana@example.com ');
    await user.type(screen.getByLabelText('Senha'), 'senha-segura-1');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(await screen.findByRole('heading', { name: 'Suas conversas' })).toBeInTheDocument();
    expect(calls.find((call) => call.path === '/auth/login')?.body).toEqual({
      email: 'ana@example.com',
      password: 'senha-segura-1',
    });
  });

  it('shows the server error and stays on the page', async () => {
    mockApi([
      ['GET', '/auth/me', () => UNAUTHENTICATED],
      [
        'POST',
        '/auth/login',
        () => ({ status: 401, body: { error: 'E-mail ou senha incorretos' } }),
      ],
    ]);
    const user = userEvent.setup();
    renderApp('/login');

    await user.type(await screen.findByLabelText('E-mail'), 'ana@example.com');
    await user.type(screen.getByLabelText('Senha'), 'errada');
    await user.click(screen.getByRole('button', { name: 'Entrar' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha incorretos');
    expect(screen.getByRole('heading', { name: 'Entrar' })).toBeInTheDocument();
  });

  it('sends signed-in users straight to their conversations', async () => {
    mockApi([
      ['GET', '/auth/me', () => ({ body: USER })],
      ['GET', '/conversations', () => ({ body: { conversations: [] } })],
    ]);
    renderApp('/login');
    expect(await screen.findByRole('heading', { name: 'Suas conversas' })).toBeInTheDocument();
  });
});

describe('sign-up', () => {
  const routes = (inviteRequired: boolean) =>
    mockApi([
      ['GET', '/auth/me', () => UNAUTHENTICATED],
      ['GET', '/config', () => ({ body: { invite_required: inviteRequired } })],
      ['POST', '/auth/register', () => ({ status: 201, body: { message: 'ok' } })],
    ]);

  it('hides the invite field unless the server requires one', async () => {
    routes(false);
    renderApp('/register');
    await screen.findByLabelText('Nome completo');
    expect(screen.queryByLabelText('Código de convite')).not.toBeInTheDocument();
  });

  it('shows the invite field when the server requires one', async () => {
    routes(true);
    renderApp('/register');
    expect(await screen.findByLabelText('Código de convite')).toBeInTheDocument();
  });

  it('registers with the profile codes and goes to the login page', async () => {
    const { calls } = routes(true);
    const user = userEvent.setup();
    renderApp('/register');

    await user.type(await screen.findByLabelText('Nome completo'), 'Ana Souza');
    await user.type(screen.getByLabelText(/E-mail/), 'ana@example.com');
    await user.type(screen.getByLabelText(/Senha/), 'senha-segura-1');
    await user.selectOptions(screen.getByLabelText('Tipo de gado'), 'Corte');
    await user.selectOptions(screen.getByLabelText('Tamanho do rebanho'), 'Médio');
    await user.type(await screen.findByLabelText('Código de convite'), 'demo-secret');
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'Entrar' })).toBeInTheDocument(),
    );
    expect(screen.getByRole('status')).toHaveTextContent('Conta criada');
    expect(calls.find((call) => call.path === '/auth/register')?.body).toEqual({
      name: 'Ana Souza',
      email: 'ana@example.com',
      password: 'senha-segura-1',
      herd_size: 'medium',
      cattle_type: 'beef',
      invite_code: 'demo-secret',
    });
  });

  it('shows the server error (for example an e-mail already registered)', async () => {
    mockApi([
      ['GET', '/auth/me', () => UNAUTHENTICATED],
      ['GET', '/config', () => ({ body: { invite_required: false } })],
      ['POST', '/auth/register', () => ({ status: 409, body: { error: 'E-mail já cadastrado' } })],
    ]);
    const user = userEvent.setup();
    renderApp('/register');

    await user.type(await screen.findByLabelText('Nome completo'), 'Ana');
    await user.type(screen.getByLabelText(/E-mail/), 'ana@example.com');
    await user.type(screen.getByLabelText(/Senha/), 'senha-segura-1');
    await user.selectOptions(screen.getByLabelText('Tipo de gado'), 'Leite');
    await user.selectOptions(screen.getByLabelText('Tamanho do rebanho'), 'Pequeno');
    await user.click(screen.getByRole('button', { name: 'Criar conta' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail já cadastrado');
  });
});

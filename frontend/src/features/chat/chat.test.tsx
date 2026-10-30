import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { mockApi, renderApp, USER } from '@/test/utils';

const CONVERSATION_ID = '5f6c1a0e-0a53-4f0a-8d10-7e2d9f6d2b11';
const MESSAGES_URL = /^\/conversations\/[0-9a-f-]{36}\/messages$/;

const LIST = {
  conversations: [
    {
      id: CONVERSATION_ID,
      title: 'Minhas vacas estão produzindo 20 litros...',
      preview: 'Para vacas de 20 L/dia...',
      created_at: '2026-10-30 10:00:00',
    },
  ],
};

function signedInApi(extra: Parameters<typeof mockApi>[0] = []) {
  return mockApi([
    ['GET', '/auth/me', () => ({ body: USER })],
    ['GET', '/conversations', () => ({ body: LIST })],
    ...extra,
  ]);
}

describe('conversation list', () => {
  it('shows the conversations and the producer profile', async () => {
    signedInApi();
    renderApp('/conversations');

    const link = await screen.findByRole('link', { name: /Minhas vacas estão produzindo/ });
    expect(link).toHaveAttribute('href', `/conversations/${CONVERSATION_ID}`);
    expect(screen.getByText('Leite · porte pequeno')).toBeInTheDocument();
  });

  it('invites the user to start the first conversation', async () => {
    mockApi([
      ['GET', '/auth/me', () => ({ body: USER })],
      ['GET', '/conversations', () => ({ body: { conversations: [] } })],
    ]);
    renderApp('/conversations');
    expect(await screen.findByText(/ainda não tem conversas/)).toBeInTheDocument();
  });

  it('opens a conversation with its history', async () => {
    signedInApi([
      [
        'GET',
        `/conversations/${CONVERSATION_ID}/messages`,
        () => ({
          body: {
            messages: [
              { question: 'Quanto de proteína?', answer: 'Cerca de **16%**.', created_at: '' },
            ],
          },
        }),
      ],
    ]);
    const user = userEvent.setup();
    renderApp('/conversations');

    await user.click(await screen.findByRole('link', { name: /Minhas vacas/ }));

    expect(await screen.findByText('Quanto de proteína?')).toBeInTheDocument();
    const answer = await screen.findByText('16%');
    expect(answer.tagName).toBe('STRONG'); // markdown rendered
  });
});

describe('chatting', () => {
  it('starts with the welcome message and the disclaimer', async () => {
    signedInApi();
    renderApp('/conversations/new');
    expect(await screen.findByText(/seja bem-vindo ao SVDA/)).toBeInTheDocument();
    expect(
      screen.getByText(/não substituem a avaliação de um médico-veterinário/),
    ).toBeInTheDocument();
  });

  it('sends a message, shows the answer and keeps the conversation after the URL changes', async () => {
    const { calls } = signedInApi([
      [
        'POST',
        MESSAGES_URL,
        (request) => ({
          body: {
            conversation_id: request.path.split('/')[2],
            answer: 'Use **proteinado**.',
            truncated: false,
          },
        }),
      ],
    ]);
    const user = userEvent.setup();
    renderApp('/conversations/new');

    await user.type(await screen.findByLabelText('Sua dúvida'), 'Como alimentar na seca?');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));

    expect(await screen.findByText('proteinado')).toBeInTheDocument();
    expect(screen.getByText('Como alimentar na seca?')).toBeInTheDocument();
    expect(screen.queryByText(/seja bem-vindo ao SVDA/)).not.toBeInTheDocument();

    const post = calls.find((call) => call.method === 'POST');
    expect(post?.body).toEqual({ message: 'Como alimentar na seca?' });
    // The first reply must not trigger a reload of the history (it would wipe the screen).
    await waitFor(() =>
      expect(
        calls.filter((call) => call.method === 'GET' && MESSAGES_URL.test(call.path)),
      ).toHaveLength(0),
    );
    expect(screen.getByText('Como alimentar na seca?')).toBeInTheDocument();
  });

  it('refreshes the conversation list after a reply', async () => {
    const { calls } = signedInApi([
      [
        'POST',
        MESSAGES_URL,
        () => ({ body: { conversation_id: 'x', answer: 'Ok.', truncated: false } }),
      ],
    ]);
    const user = userEvent.setup();
    renderApp('/conversations/new');
    await user.type(await screen.findByLabelText('Sua dúvida'), 'Oi');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    await screen.findByText('Ok.');
    await waitFor(() =>
      expect(calls.filter((call) => call.path === '/conversations')).toHaveLength(2),
    );
  });

  it('warns when the answer was cut by the size limit', async () => {
    signedInApi([
      [
        'POST',
        MESSAGES_URL,
        () => ({ body: { conversation_id: 'x', answer: 'Resposta longa', truncated: true } }),
      ],
    ]);
    const user = userEvent.setup();
    renderApp('/conversations/new');
    await user.type(await screen.findByLabelText('Sua dúvida'), 'Dieta completa');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(await screen.findByText(/cortada pelo limite de tamanho/)).toBeInTheDocument();
  });

  it('shows the server message when the assistant is unavailable', async () => {
    signedInApi([
      [
        'POST',
        MESSAGES_URL,
        () => ({ status: 503, body: { error: 'O assistente está muito ocupado agora.' } }),
      ],
    ]);
    const user = userEvent.setup();
    renderApp('/conversations/new');
    await user.type(await screen.findByLabelText('Sua dúvida'), 'Oi');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(await screen.findByText('O assistente está muito ocupado agora.')).toBeInTheDocument();
  });

  it('does not send empty messages', async () => {
    const { calls } = signedInApi();
    const user = userEvent.setup();
    renderApp('/conversations/new');
    const send = await screen.findByRole('button', { name: 'Enviar' });
    expect(send).toBeDisabled();
    await user.type(screen.getByLabelText('Sua dúvida'), '   ');
    expect(send).toBeDisabled();
    expect(calls.some((call) => call.method === 'POST')).toBe(false);
  });

  it('never executes HTML in assistant answers or in the user text', async () => {
    const payload =
      'Resposta <img src=x onerror="window.__pwned=1"> <script>window.__pwned=2</script> [link](javascript:alert(1))';
    signedInApi([
      [
        'POST',
        MESSAGES_URL,
        () => ({ body: { conversation_id: 'x', answer: payload, truncated: false } }),
      ],
    ]);
    const user = userEvent.setup();
    renderApp('/conversations/new');

    await user.type(await screen.findByLabelText('Sua dúvida'), '<b>negrito?</b>');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));

    const log = await screen.findByRole('log');
    await waitFor(() => expect(within(log).getByText(/Resposta/)).toBeInTheDocument());
    expect(log.querySelector('img')).toBeNull();
    expect(log.querySelector('script')).toBeNull();
    expect(log.querySelector('b')).toBeNull();
    expect(log.querySelector('a[href^="javascript"]')).toBeNull();
    expect((window as unknown as { __pwned?: number }).__pwned).toBeUndefined();
    expect(within(log).getByText('<b>negrito?</b>')).toBeInTheDocument();
  });
});

describe('session', () => {
  it('signs out and returns to the login page', async () => {
    const { calls } = signedInApi([['POST', '/auth/logout', () => ({ body: { message: 'ok' } })]]);
    const user = userEvent.setup();
    renderApp('/conversations');

    await user.click(await screen.findByRole('button', { name: 'Sair' }));

    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument();
    expect(calls.some((call) => call.path === '/auth/logout')).toBe(true);
  });

  it('returns to the login page when the session expires mid-use', async () => {
    mockApi([
      ['GET', '/auth/me', () => ({ body: USER })],
      ['GET', '/conversations', () => ({ body: LIST })],
      ['POST', MESSAGES_URL, () => ({ status: 401, body: { error: 'Usuário não autenticado' } })],
    ]);
    const user = userEvent.setup();
    renderApp('/conversations/new');
    await user.type(await screen.findByLabelText('Sua dúvida'), 'Oi');
    await user.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument();
  });
});

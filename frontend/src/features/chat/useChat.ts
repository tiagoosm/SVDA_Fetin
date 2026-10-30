import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '@/lib/api';
import { uuid } from '@/lib/id';
import { chatApi } from './chatApi';
import type { ChatMessage } from './types';
import { TRUNCATED_NOTICE } from './welcome';

export type ChatStatus = 'loading' | 'idle' | 'sending';

interface UseChatOptions {
  conversationId: string;
  /** True for a conversation that has no messages yet (nothing to load). */
  isDraft: boolean;
  /** Called after the assistant answered (the conversation now exists on the server). */
  onReplied: () => void;
}

function toMessages(stored: { question: string; answer: string }[]): ChatMessage[] {
  return stored.flatMap(({ question, answer }) => [
    { id: uuid(), role: 'user' as const, content: question },
    { id: uuid(), role: 'assistant' as const, content: answer },
  ]);
}

/** Messages of one conversation. Mount it with `key={conversationId}` so each conversation gets fresh state. */
export function useChat({ conversationId, isDraft, onReplied }: UseChatOptions) {
  // Only the state at mount matters: a draft turns into a real conversation after the first reply,
  // and the history must not be fetched again (it would replace what is on screen).
  const [startedAsDraft] = useState(isDraft);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>(startedAsDraft ? 'idle' : 'loading');

  useEffect(() => {
    if (startedAsDraft) return;
    const controller = new AbortController();
    chatApi
      .messages(conversationId, controller.signal)
      .then((data) => setMessages(toMessages(data.messages)))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const content =
          error instanceof ApiError ? error.message : 'Não foi possível carregar a conversa.';
        setMessages([{ id: uuid(), role: 'system', content }]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setStatus('idle');
      });
    return () => controller.abort();
  }, [conversationId, startedAsDraft]);

  const send = useCallback(
    async (text: string) => {
      setMessages((current) => [...current, { id: uuid(), role: 'user', content: text }]);
      setStatus('sending');
      try {
        const reply = await chatApi.send(conversationId, text);
        setMessages((current) => [
          ...current,
          { id: uuid(), role: 'assistant', content: reply.answer, typing: true },
          ...(reply.truncated
            ? [{ id: uuid(), role: 'system' as const, content: TRUNCATED_NOTICE }]
            : []),
        ]);
        onReplied();
      } catch (error) {
        const content =
          error instanceof ApiError
            ? error.message
            : 'Não foi possível enviar a mensagem. Tente novamente.';
        setMessages((current) => [...current, { id: uuid(), role: 'system', content }]);
      } finally {
        setStatus('idle');
      }
    },
    [conversationId, onReplied],
  );

  return { messages, status, send };
}

import { useCallback, useEffect, useState } from 'react';
import type { ConversationSummary } from '@/types/api';
import { chatApi } from './chatApi';

export type ConversationsStatus = 'loading' | 'ready' | 'error';

/** The user's conversation list, newest first. */
export function useConversations() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [status, setStatus] = useState<ConversationsStatus>('loading');

  const reload = useCallback(async () => {
    try {
      const data = await chatApi.conversations();
      setConversations(data.conversations);
      setStatus('ready');
    } catch {
      setStatus((current) => (current === 'ready' ? 'ready' : 'error'));
    }
  }, []);

  useEffect(() => {
    // Fetch on mount; the state is set after the request resolves.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void reload();
  }, [reload]);

  return { conversations, status, reload };
}

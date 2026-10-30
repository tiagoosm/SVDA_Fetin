import { request } from '@/lib/api';
import type { ConversationSummary, SendMessageResponse, StoredMessage } from '@/types/api';

export const chatApi = {
  conversations: () => request<{ conversations: ConversationSummary[] }>('/conversations'),
  messages: (conversationId: string, signal?: AbortSignal) =>
    request<{ messages: StoredMessage[] }>(
      `/conversations/${encodeURIComponent(conversationId)}/messages`,
      {
        signal,
      },
    ),
  send: (conversationId: string, message: string) =>
    request<SendMessageResponse>(`/conversations/${encodeURIComponent(conversationId)}/messages`, {
      method: 'POST',
      body: { message },
    }),
};

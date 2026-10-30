export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  /** Reveal the content with the typing effect (only for answers that just arrived). */
  typing?: boolean;
}

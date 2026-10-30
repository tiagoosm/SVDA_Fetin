import { useCallback, useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import type { ChatStatus } from './useChat';
import type { ChatMessage } from './types';
import { WELCOME_MESSAGE } from './welcome';

const NEAR_BOTTOM_PX = 140;

interface MessageListProps {
  messages: ChatMessage[];
  status: ChatStatus;
}

const WELCOME: ChatMessage = { id: 'welcome', role: 'assistant', content: WELCOME_MESSAGE };

export function MessageList({ messages, status }: MessageListProps) {
  const container = useRef<HTMLDivElement>(null);

  const scrollToEnd = useCallback(() => {
    const element = container.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, []);

  // While an answer is being typed, follow it only if the reader is already at the bottom.
  const followTyping = useCallback(() => {
    const element = container.current;
    if (!element) return;
    if (element.scrollHeight - element.scrollTop - element.clientHeight < NEAR_BOTTOM_PX)
      scrollToEnd();
  }, [scrollToEnd]);

  useEffect(() => {
    scrollToEnd();
  }, [messages, status, scrollToEnd]);

  const isEmpty = messages.length === 0 && status !== 'loading';

  return (
    <div
      ref={container}
      role="log"
      aria-live="polite"
      aria-label="Mensagens da conversa"
      className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-6 sm:px-[clamp(1rem,5vw,4.5rem)]"
    >
      {status === 'loading' ? (
        <p role="status" className="self-center text-sm text-muted">
          Carregando conversa…
        </p>
      ) : null}
      {isEmpty ? <MessageBubble message={WELCOME} onTypingProgress={followTyping} /> : null}
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} onTypingProgress={followTyping} />
      ))}
      {status === 'sending' ? (
        <div role="status" aria-label="O assistente está respondendo" className="max-w-fit">
          <div className="flex gap-1.5 rounded-[1.6rem] rounded-bl-lg bg-white px-5 py-4 shadow-[0_10px_30px_-18px_rgba(34,64,46,0.5)]">
            {[0, 150, 300].map((delay) => (
              <span
                key={delay}
                style={{ animationDelay: `${delay}ms` }}
                className="size-2 rounded-full bg-moss motion-safe:animate-dot"
              />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

import clsx from 'clsx';
import { memo, useEffect, useRef } from 'react';
import type { ComponentProps } from 'react';
import Markdown from 'react-markdown';
import { typeInto } from '@/lib/typewriter';
import type { ChatMessage } from './types';

function ExternalLink({ href, children }: ComponentProps<'a'>) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  );
}

/** Renders markdown as React elements. Raw HTML in the text is never interpreted. */
const MarkdownBody = memo(function MarkdownBody({ text }: { text: string }) {
  return <Markdown components={{ a: ExternalLink }}>{text}</Markdown>;
});

const prefersReducedMotion = () =>
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

interface AssistantBodyProps {
  text: string;
  typing: boolean;
  onProgress: () => void;
}

function AssistantBody({ text, typing, onProgress }: AssistantBodyProps) {
  const ref = useRef<HTMLDivElement>(null);
  const progress = useRef(onProgress);

  useEffect(() => {
    progress.current = onProgress;
  });

  useEffect(() => {
    if (!typing || !ref.current || prefersReducedMotion()) return;
    return typeInto(ref.current, { onProgress: () => progress.current() });
  }, [typing]);

  return (
    <div ref={ref} className="markdown">
      <MarkdownBody text={text} />
    </div>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
  onTypingProgress: () => void;
}

export const MessageBubble = memo(function MessageBubble({
  message,
  onTypingProgress,
}: MessageBubbleProps) {
  if (message.role === 'system') {
    return (
      <p
        role="status"
        className="self-center rounded-full bg-sky px-4 py-1.5 text-center text-sm font-medium text-moss"
      >
        {message.content}
      </p>
    );
  }

  const isUser = message.role === 'user';
  return (
    <div className={clsx('max-w-[min(41rem,90%)]', isUser && 'self-end')}>
      <div
        className={clsx(
          'px-5 py-3.5 leading-relaxed break-words',
          isUser
            ? 'rounded-[1.6rem] rounded-br-lg bg-moss whitespace-pre-wrap text-white'
            : 'rounded-[1.6rem] rounded-bl-lg bg-white shadow-[0_10px_30px_-18px_rgba(34,64,46,0.5)]',
        )}
      >
        {isUser ? (
          message.content
        ) : (
          <AssistantBody
            text={message.content}
            typing={message.typing === true}
            onProgress={onTypingProgress}
          />
        )}
      </div>
    </div>
  );
});

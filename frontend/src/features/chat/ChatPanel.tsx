import clsx from 'clsx';
import { Link } from 'react-router';
import { ArrowLeftIcon } from '@/components/ui/icons';
import { ContourBackground } from '@/components/ui/Contour';
import { Composer } from './Composer';
import { MessageList } from './MessageList';
import { useChat } from './useChat';

interface ChatPanelProps {
  conversationId: string;
  isDraft: boolean;
  title: string;
  /** "Leite · Pequeno" */
  profile: string | null;
  className?: string;
  onReplied: () => void;
}

export function ChatPanel({
  conversationId,
  isDraft,
  title,
  profile,
  className,
  onReplied,
}: ChatPanelProps) {
  const { messages, status, send } = useChat({ conversationId, isDraft, onReplied });

  return (
    <section
      aria-label="Conversa"
      className={clsx('relative isolate min-h-0 min-w-0 flex-col', className)}
    >
      <ContourBackground />
      <header className="flex items-center gap-2 bg-white/70 px-3.5 py-3 backdrop-blur-md">
        <Link
          to="/conversations"
          aria-label="Voltar para as conversas"
          className="grid size-12 place-items-center rounded-full text-moss hover:bg-moss/10 md:hidden"
        >
          <ArrowLeftIcon />
        </Link>
        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-3 gap-y-1">
          <h2 className="max-w-full truncate font-display text-2xl font-bold text-moss">{title}</h2>
          {profile ? (
            <span className="rounded-full bg-sky px-3 py-0.5 text-[0.8125rem] font-semibold whitespace-nowrap text-moss">
              {profile}
            </span>
          ) : null}
        </div>
      </header>
      <MessageList messages={messages} status={status} />
      <Composer disabled={status !== 'idle'} onSend={(text) => void send(text)} />
    </section>
  );
}

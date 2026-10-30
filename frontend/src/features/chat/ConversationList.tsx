import clsx from 'clsx';
import { NavLink } from 'react-router';
import { ContourThumb } from '@/components/ui/Contour';
import { plainText } from '@/lib/text';
import type { ConversationSummary } from '@/types/api';
import type { ConversationsStatus } from './useConversations';

interface ConversationListProps {
  conversations: ConversationSummary[];
  status: ConversationsStatus;
}

export function ConversationList({ conversations, status }: ConversationListProps) {
  if (status === 'loading') {
    return (
      <p role="status" className="px-2 text-sm text-mist">
        Carregando conversas…
      </p>
    );
  }
  if (status === 'error') {
    return (
      <p role="alert" className="px-2 text-sm text-mist">
        Não foi possível carregar suas conversas. Tente recarregar a página.
      </p>
    );
  }
  if (conversations.length === 0) {
    return (
      <p className="px-2 text-sm text-mist">
        Você ainda não tem conversas. Toque em “Nova conversa” para tirar sua primeira dúvida.
      </p>
    );
  }

  return (
    <ul className="grid gap-2.5">
      {conversations.map((conversation) => (
        <li key={conversation.id}>
          <NavLink
            to={`/conversations/${conversation.id}`}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3.5 rounded-[1.4rem] p-3 transition-colors',
                isActive
                  ? 'bg-white/15 shadow-[inset_4px_0_0_var(--color-sun)]'
                  : 'bg-white/7 hover:bg-white/12',
              )
            }
          >
            <span className="size-15 shrink-0 overflow-hidden rounded-2xl bg-moss-light text-sun">
              <ContourThumb seed={conversation.id} />
            </span>
            <span className="min-w-0">
              <strong className="line-clamp-2 text-base leading-tight font-bold">
                {conversation.title}
              </strong>
              <span className="mt-0.5 line-clamp-2 text-sm text-mist">
                {plainText(conversation.preview)}
              </span>
            </span>
          </NavLink>
        </li>
      ))}
    </ul>
  );
}

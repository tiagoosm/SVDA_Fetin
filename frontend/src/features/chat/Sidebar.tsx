import clsx from 'clsx';
import { BullMark } from '@/components/ui/BullMark';
import { ContourBackground } from '@/components/ui/Contour';
import { LogoutIcon, PlusIcon } from '@/components/ui/icons';
import { profileSentence } from '@/lib/labels';
import type { User } from '@/types/api';
import { ConversationList } from './ConversationList';
import type { ConversationsStatus } from './useConversations';
import type { ConversationSummary } from '@/types/api';

interface SidebarProps {
  user: User | null;
  conversations: ConversationSummary[];
  status: ConversationsStatus;
  className?: string;
  onNewConversation: () => void;
  onLogout: () => void;
}

export function Sidebar({
  user,
  conversations,
  status,
  className,
  onNewConversation,
  onLogout,
}: SidebarProps) {
  const profile = profileSentence(user);

  return (
    <aside
      aria-label="Suas conversas"
      className={clsx(
        'on-dark relative isolate min-h-0 flex-col gap-4 bg-moss p-4 pt-5 text-[#eaf2e4]',
        className,
      )}
    >
      <ContourBackground variant="dark" />
      <div className="flex items-center justify-between gap-3">
        <span className="flex items-center gap-2.5">
          <BullMark decorative className="w-11 text-sun" />
          <span className="font-display text-3xl font-extrabold tracking-tight">SVDA</span>
        </span>
        <button
          type="button"
          onClick={onLogout}
          aria-label="Sair"
          className="grid size-12 place-items-center rounded-full bg-white/10 transition-colors hover:bg-white/20"
        >
          <LogoutIcon />
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-[1.75rem] leading-tight font-bold">Suas conversas</h2>
        <button
          type="button"
          onClick={onNewConversation}
          className="inline-flex min-h-12 items-center gap-2 rounded-full bg-sun px-5 font-bold text-moss transition hover:brightness-95"
        >
          <PlusIcon />
          Nova conversa
        </button>
      </div>

      <nav aria-label="Conversas" className="min-h-0 flex-1 overflow-y-auto">
        <ConversationList conversations={conversations} status={status} />
      </nav>

      {profile ? (
        <p className="flex flex-col rounded-2xl bg-black/20 px-3.5 py-3">
          <span className="text-[0.8125rem] text-mist">Seu rebanho</span>
          <strong className="font-semibold">{profile}</strong>
        </p>
      ) : null}
    </aside>
  );
}

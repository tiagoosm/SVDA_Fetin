import { useCallback, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { useAuth } from '@/context/auth-context';
import { uuid } from '@/lib/id';
import { profileChip } from '@/lib/labels';
import { ChatPanel } from './ChatPanel';
import { Sidebar } from './Sidebar';
import { useConversations } from './useConversations';

/**
 * The signed-in app: conversation list + chat.
 *   /conversations        list (on phones) / a new conversation (on wider screens)
 *   /conversations/new    a new conversation
 *   /conversations/:id    an existing conversation
 * Tablets and wider show both panes; phones show one at a time.
 */
export function ChatApp() {
  const { conversationId: routeId } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { conversations, status, reload } = useConversations();

  // A new conversation gets its id up front (the server accepts any UUID); the draft id
  // keeps the chat panel mounted when the URL changes after the first reply.
  const [draftId, setDraftId] = useState(uuid);
  const isDraft = routeId === undefined || routeId === 'new';
  const conversationId = isDraft ? draftId : routeId;
  const showChatOnMobile = routeId !== undefined;

  const handleReplied = useCallback(() => {
    void reload();
    if (isDraft) navigate(`/conversations/${draftId}`, { replace: true });
  }, [reload, isDraft, navigate, draftId]);

  function startNewConversation() {
    setDraftId(uuid());
    navigate('/conversations/new');
  }

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  const title = isDraft
    ? 'Nova conversa'
    : (conversations.find((conversation) => conversation.id === conversationId)?.title ??
      'Conversa');

  return (
    <div className="grid h-dvh grid-cols-1 md:grid-cols-[minmax(18rem,23.75rem)_minmax(0,1fr)]">
      <Sidebar
        user={user}
        conversations={conversations}
        status={status}
        className={showChatOnMobile ? 'hidden md:flex' : 'flex'}
        onNewConversation={startNewConversation}
        onLogout={() => void handleLogout()}
      />
      <ChatPanel
        key={conversationId}
        conversationId={conversationId}
        isDraft={isDraft}
        title={title}
        profile={profileChip(user)}
        className={showChatOnMobile ? 'flex' : 'hidden md:flex'}
        onReplied={handleReplied}
      />
    </div>
  );
}

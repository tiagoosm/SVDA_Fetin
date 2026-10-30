import { Navigate, Route, Routes } from 'react-router';
import { LoginPage } from '@/features/auth/LoginPage';
import { RegisterPage } from '@/features/auth/RegisterPage';
import { ChatApp } from '@/features/chat/ChatApp';
import { PublicOnly } from '@/routes/PublicOnly';
import { RequireAuth } from '@/routes/RequireAuth';

export function App() {
  return (
    <Routes>
      <Route element={<PublicOnly />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route element={<RequireAuth />}>
        <Route path="/conversations/:conversationId?" element={<ChatApp />} />
      </Route>
      <Route path="*" element={<Navigate to="/conversations" replace />} />
    </Routes>
  );
}

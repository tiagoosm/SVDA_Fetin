/** Shapes exchanged with the SVDA API (see backend/app/routes). */

export type HerdSize = 'small' | 'medium' | 'large';
export type CattleType = 'dairy' | 'beef' | 'other';

export interface User {
  id: number;
  email: string;
  name: string | null;
  herd_size: HerdSize | null;
  cattle_type: CattleType | null;
}

export interface RegisterPayload {
  email: string;
  password: string;
  name: string;
  herd_size: HerdSize;
  cattle_type: CattleType;
  invite_code?: string;
}

export interface PublicConfig {
  invite_required: boolean;
}

export interface ConversationSummary {
  id: string;
  title: string;
  preview: string;
  created_at: string;
}

export interface StoredMessage {
  question: string;
  answer: string;
  created_at: string;
}

export interface SendMessageResponse {
  conversation_id: string;
  answer: string;
  truncated: boolean;
}

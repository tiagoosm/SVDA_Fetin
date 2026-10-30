import type { CattleType, HerdSize, User } from '@/types/api';

export const HERD_SIZE_LABELS: Record<HerdSize, string> = {
  small: 'Pequeno',
  medium: 'Médio',
  large: 'Grande',
};

export const CATTLE_TYPE_LABELS: Record<CattleType, string> = {
  dairy: 'Leite',
  beef: 'Corte',
  other: 'Outro',
};

/** "Leite · Pequeno", or null for accounts created before the profile existed. */
export function profileChip(user: User | null): string | null {
  if (!user?.cattle_type || !user.herd_size) return null;
  return `${CATTLE_TYPE_LABELS[user.cattle_type]} · ${HERD_SIZE_LABELS[user.herd_size]}`;
}

/** "Leite · porte pequeno". */
export function profileSentence(user: User | null): string | null {
  if (!user?.cattle_type || !user.herd_size) return null;
  return `${CATTLE_TYPE_LABELS[user.cattle_type]} · porte ${HERD_SIZE_LABELS[user.herd_size].toLowerCase()}`;
}

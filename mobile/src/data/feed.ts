import { generateFeedOutfits, type Outfit } from '@/lib/outfits';

import type { StyleId } from './styles';
import type { Department } from './taxonomy';

export type FeedPage = {
  items: Outfit[];
  nextCursor: number | null;
};

const PAGE_SIZE = 3;
const LATENCY_MS = 600;

// Мок бэкенда ленты: образы собирает движок lib/outfits из каталога под профиль пользователя,
// отдаём их курсорными страницами с задержкой. Когда появится API, заменяется только тело
// этой функции — сигнатура остаётся.
export async function fetchFeedPage(
  cursor: number,
  profile: { department: Department; styles: StyleId[] },
  pageSize = PAGE_SIZE,
): Promise<FeedPage> {
  await new Promise((resolve) => setTimeout(resolve, LATENCY_MS));

  const outfits = generateFeedOutfits(profile.department, profile.styles);
  const next = cursor + pageSize;

  return { items: outfits.slice(cursor, next), nextCursor: next < outfits.length ? next : null };
}

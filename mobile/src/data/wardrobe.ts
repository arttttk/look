import { type Category, type ColorId, categoryTitle, isCategory, isColorId } from './taxonomy';

export type WardrobeItem = {
  id: string;
  category: Category;
  color: ColorId;
  // Необязательное название от пользователя; если пусто — показываем категорию.
  title: string;
  image: string;
  createdAt: number;
};

export const itemLabel = (item: WardrobeItem) => item.title.trim() || categoryTitle(item.category);

export function newItemId() {
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
}

// Данные приходят из хранилища — отбрасываем всё, что не похоже на вещь.
export function parseWardrobe(raw: unknown): WardrobeItem[] {
  if (!Array.isArray(raw)) return [];

  return raw.flatMap((entry): WardrobeItem[] => {
    if (!entry || typeof entry !== 'object') return [];
    const { id, category, color, title, image, createdAt } = entry as Record<string, unknown>;
    if (typeof id !== 'string' || typeof image !== 'string') return [];
    if (!isCategory(category) || !isColorId(color)) return [];

    return [
      {
        id,
        category,
        color,
        title: typeof title === 'string' ? title : '',
        image,
        createdAt: typeof createdAt === 'number' ? createdAt : 0,
      },
    ];
  });
}

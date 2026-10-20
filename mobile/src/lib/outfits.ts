import { catalogFor, productById, type Product } from '@/data/catalog';
import type { StyleId } from '@/data/styles';
import { type Category, type ColorId, type Department, colorById } from '@/data/taxonomy';
import { itemLabel, type WardrobeItem } from '@/data/wardrobe';
import { formatPrice, plural } from '@/lib/format';

// Автоподбор образов — чистые функции без React и сети. Бэкенд потом может повторить
// эту же логику на сервере; сигнатуры и формат id (resolveOutfit) при этом сохраняются.

export type Piece = {
  id: string; // 'c.<productId>' — из каталога, 'w.<itemId>' — из гардероба
  origin: 'catalog' | 'wardrobe';
  category: Category;
  title: string;
  color: ColorId;
  styles: StyleId[]; // у вещей гардероба пусто: стиль мы им пока не определяем
  image?: string;
  product?: Product;
};

export type Outfit = {
  id: string;
  title: string;
  styles: StyleId[];
  pieces: Piece[];
  score: number;
};

export const pieceFromProduct = (product: Product): Piece => ({
  id: `c.${product.id}`,
  origin: 'catalog',
  category: product.category,
  title: product.title,
  color: product.color,
  styles: product.styles,
  image: product.image,
  product,
});

export const pieceFromItem = (item: WardrobeItem): Piece => ({
  id: `w.${item.id}`,
  origin: 'wardrobe',
  category: item.category,
  title: itemLabel(item),
  color: item.color,
  styles: [],
  image: item.image,
});

// Вещи образа, которых нет в гардеробе и которые можно купить по реферальной ссылке.
export const piecesToBuy = (outfit: Outfit) => outfit.pieces.filter((piece) => piece.origin === 'catalog');

// Подпись под образом: что из него уже есть, а что придётся купить.
export function describeOutfit(outfit: Outfit): string {
  const toBuy = piecesToBuy(outfit);
  const total = formatPrice(toBuy.reduce((sum, piece) => sum + (piece.product?.price ?? 0), 0));

  if (!outfit.pieces.some((piece) => piece.origin === 'wardrobe')) return `Весь образ · ${total}`;
  if (toBuy.length === 0) return 'Всё из вашего гардероба';
  return `Докупить ${toBuy.length} ${plural(toBuy.length, ['вещь', 'вещи', 'вещей'])} · ${total}`;
}

const ORDER: Category[] = ['outerwear', 'top', 'bottom', 'shoes'];
const REQUIRED: Category[] = ['top', 'bottom', 'shoes'];
const MAX_PER_CATEGORY = 12;
const FILL_PER_CATEGORY = 3;
const FEED_SIZE = 80;

// Сочетания, которые считаются не лучшими: небольшой штраф.
const CLASHES: [ColorId, ColorId][] = [
  ['navy', 'black'],
  ['brown', 'black'],
];

const TITLES: Record<StyleId, string[]> = {
  minimal: ['Городской минимализм', 'Чистые линии', 'Тихая роскошь', 'Монохромный ритм', 'Ничего лишнего'],
  street: ['Уличный ритм', 'Свободный крой', 'Городской стритвир', 'Асфальт и неон', 'Район и музыка'],
  classic: ['Классика без лишнего', 'Офисная классика', 'Строгий силуэт', 'Деловой выход', 'Вне времени'],
  casual: ['Лёгкий кэжуал', 'Удобно и просто', 'Выходной образ', 'Мягкий день', 'Без усилий'],
  sport: ['Активный день', 'Спорт-шик', 'Динамика', 'Тренировка и кофе', 'В движении'],
  vintage: ['Осенний винтаж', 'Ретро-настроение', 'Тёплый слой', 'Привет из 90-х', 'Антикварная лавка'],
};

export const occasions: { tag: string; styles: StyleId[] }[] = [
  { tag: 'Работа', styles: ['classic', 'minimal'] },
  { tag: 'Учёба', styles: ['casual', 'street'] },
  { tag: 'Прогулка', styles: ['street', 'casual', 'vintage'] },
  { tag: 'Вечер', styles: ['classic', 'vintage', 'minimal'] },
  { tag: 'Спорт', styles: ['sport'] },
  { tag: 'Выходные', styles: ['casual', 'vintage'] },
];

function hash(text: string) {
  let value = 0;
  for (let i = 0; i < text.length; i++) value = (value * 31 + text.charCodeAt(i)) >>> 0;
  return value;
}

// Не больше одного акцентного цвета; нейтральная база — плюс.
function colorScore(pieces: Piece[]) {
  const colors = pieces.map((piece) => piece.color);
  const accents = new Set(colors.filter((color) => !colorById(color).neutral));

  let score = accents.size === 0 ? 1 : -(accents.size - 1) * 3;
  for (const [a, b] of CLASHES) {
    if (colors.includes(a) && colors.includes(b)) score -= 0.5;
  }
  return score;
}

// Стиль образа — тот, что совпал минимум у двух вещей; при равенстве выигрывают стили пользователя.
function dominantStyles(pieces: Piece[], preferred: StyleId[]) {
  const counts = new Map<StyleId, number>();
  for (const piece of pieces) {
    for (const style of piece.styles) counts.set(style, (counts.get(style) ?? 0) + 1);
  }

  const max = Math.max(0, ...counts.values());
  if (max < 2) return { styles: [] as StyleId[], cohesion: 0 };

  const styles = [...counts]
    .filter(([, count]) => count === max)
    .map(([style]) => style)
    .sort((a, b) => Number(preferred.includes(b)) - Number(preferred.includes(a)) || a.localeCompare(b))
    .slice(0, 2);

  return { styles, cohesion: max };
}

function titleFor(id: string, styles: StyleId[], pieces: Piece[]) {
  if (styles.length > 0) {
    const names = TITLES[styles[0]];
    return names[hash(id) % names.length];
  }

  const colors = [...new Set(pieces.map((piece) => piece.color))];
  if (colors.length === 1) {
    const color = colors[0];
    if (color === 'black') return 'Total black';
    if (color === 'white') return 'Total white';
    return `Монохром: ${colorById(color).title.toLowerCase()}`;
  }

  const accent = colors.find((color) => !colorById(color).neutral);
  return accent ? `Акцент: ${colorById(accent).title.toLowerCase()}` : 'Нейтральная база';
}

function buildOutfit(pieces: Piece[], userStyles: StyleId[]): Outfit {
  const sorted = [...pieces].sort((a, b) => ORDER.indexOf(a.category) - ORDER.indexOf(b.category));
  const id = sorted.map((piece) => piece.id).join('~');
  const { styles, cohesion } = dominantStyles(sorted, userStyles);

  const personal = styles.filter((style) => userStyles.includes(style)).length;
  const outerwear = sorted.some((piece) => piece.category === 'outerwear') ? 0.5 : 0;

  return {
    id,
    title: titleFor(id, styles, sorted),
    styles,
    pieces: sorted,
    score: colorScore(sorted) + cohesion + personal * 2 + outerwear,
  };
}

function combine(pools: Record<Category, Piece[]>): Piece[][] {
  const outerOptions: (Piece | null)[] = [null, ...pools.outerwear];
  const result: Piece[][] = [];

  for (const top of pools.top) {
    for (const bottom of pools.bottom) {
      for (const shoes of pools.shoes) {
        for (const outer of outerOptions) {
          result.push(outer ? [outer, top, bottom, shoes] : [top, bottom, shoes]);
        }
      }
    }
  }

  // Явно конфликтующие по цвету образы убираем, если есть из чего выбирать.
  const harmonious = result.filter((pieces) => colorScore(pieces) >= 0);
  return harmonious.length > 0 ? harmonious : result;
}

// Лучшие образы вперёд, но одна и та же вещь не должна занимать всю ленту:
// сначала берём образы, где каждая вещь встречается не больше maxUses раз, потом добираем остальные.
function pickDiverse(outfits: Outfit[], limit: number, maxUses = 2): Outfit[] {
  const sorted = [...outfits].sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
  const uses = new Map<string, number>();
  const picked: Outfit[] = [];
  const chosen = new Set<string>();

  const take = (outfit: Outfit) => {
    picked.push(outfit);
    chosen.add(outfit.id);
    for (const piece of outfit.pieces) uses.set(piece.id, (uses.get(piece.id) ?? 0) + 1);
  };

  for (const outfit of sorted) {
    if (picked.length >= limit) break;
    if (outfit.pieces.every((piece) => (uses.get(piece.id) ?? 0) < maxUses)) take(outfit);
  }
  for (const outfit of sorted) {
    if (picked.length >= limit) break;
    if (!chosen.has(outfit.id)) take(outfit);
  }
  return picked;
}

const emptyPools = (): Record<Category, Piece[]> => ({
  outerwear: [],
  top: [],
  bottom: [],
  shoes: [],
  accessory: [],
});

const feedCache = new Map<string, Outfit[]>();

// Лента: образы целиком из каталога, отранжированные под стили пользователя.
export function generateFeedOutfits(department: Department, userStyles: StyleId[]): Outfit[] {
  const key = `${department}|${[...userStyles].sort().join(',')}`;
  const cached = feedCache.get(key);
  if (cached) return cached;

  const pools = emptyPools();
  for (const product of catalogFor(department)) pools[product.category].push(pieceFromProduct(product));

  const outfits = combine(pools).map((pieces) => buildOutfit(pieces, userStyles));
  const result = pickDiverse(outfits, FEED_SIZE);

  feedCache.set(key, result);
  return result;
}

// Образы из гардероба пользователя. Если в обязательной категории (верх/низ/обувь) у него пусто,
// слот закрывается вещью из каталога — её можно купить по реферальной ссылке.
export function generateWardrobeOutfits(
  items: WardrobeItem[],
  department: Department,
  userStyles: StyleId[],
  limit = 12,
): Outfit[] {
  if (items.length === 0) return [];

  const store = catalogFor(department).map(pieceFromProduct);
  const own = [...items].sort((a, b) => b.createdAt - a.createdAt).map(pieceFromItem);
  const pools = emptyPools();

  for (const category of ORDER) {
    const mine = own.filter((piece) => piece.category === category).slice(0, MAX_PER_CATEGORY);
    if (mine.length > 0 || !REQUIRED.includes(category)) {
      pools[category] = mine;
      continue;
    }

    const overlap = (piece: Piece) => piece.styles.filter((style) => userStyles.includes(style)).length;
    pools[category] = store
      .filter((piece) => piece.category === category)
      .sort((a, b) => overlap(b) - overlap(a) || a.id.localeCompare(b.id))
      .slice(0, FILL_PER_CATEGORY);
  }

  // Свои вещи важнее: каждая вещь «на покупку» сильно снижает оценку образа.
  const outfits = combine(pools).map((pieces) => {
    const outfit = buildOutfit(pieces, userStyles);
    const toBuy = piecesToBuy(outfit).length;
    const outerwear = outfit.pieces.some((piece) => piece.category === 'outerwear') ? 0.5 : 0;
    return { ...outfit, score: colorScore(outfit.pieces) + outerwear - toBuy * 3 };
  });

  return pickDiverse(outfits, limit);
}

// Категории, которых не хватает в гардеробе для полного образа, и что можно докупить.
export function missingCategories(items: WardrobeItem[]): Category[] {
  return REQUIRED.filter((category) => !items.some((item) => item.category === category));
}

export function suggestProducts(
  category: Category,
  department: Department,
  userStyles: StyleId[],
  limit = 4,
): Product[] {
  const overlap = (product: Product) => product.styles.filter((style) => userStyles.includes(style)).length;
  return catalogFor(department)
    .filter((product) => product.category === category)
    .sort((a, b) => overlap(b) - overlap(a) || a.price - b.price)
    .slice(0, limit);
}

// Образ целиком восстанавливается из id: он хранит id вещей каталога и гардероба.
// null — если какой-то вещи уже нет (например, удалили из гардероба).
export function resolveOutfit(id: string, wardrobe: WardrobeItem[], userStyles: StyleId[]): Outfit | null {
  const pieces: Piece[] = [];

  for (const token of id.split('~')) {
    if (token.startsWith('c.')) {
      const product = productById(token.slice(2));
      if (!product) return null;
      pieces.push(pieceFromProduct(product));
    } else if (token.startsWith('w.')) {
      const item = wardrobe.find((entry) => entry.id === token.slice(2));
      if (!item) return null;
      pieces.push(pieceFromItem(item));
    } else {
      return null;
    }
  }

  return pieces.length > 0 ? buildOutfit(pieces, userStyles) : null;
}

// Подборка «Рекомендации для вас»: по лучшему образу на каждый повод, без повторов.
export function generateOccasionOutfits(department: Department, userStyles: StyleId[]) {
  const pool = generateFeedOutfits(department, userStyles);
  const used = new Set<string>();
  const result: { tag: string; outfit: Outfit }[] = [];

  for (const occasion of occasions) {
    const outfit = pool.find(
      (candidate) => !used.has(candidate.id) && candidate.styles.some((style) => occasion.styles.includes(style)),
    );
    if (!outfit) continue;

    used.add(outfit.id);
    result.push({ tag: occasion.tag, outfit });
  }
  return result;
}

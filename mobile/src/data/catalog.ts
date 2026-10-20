import type { StyleId } from './styles';
import type { Category, ColorId, Department } from './taxonomy';

// Вещь из каталога партнёров. `url` — реферальная ссылка (мок), открывается через lib/affiliate.
// `image` пока пустой: в коллажах рисуется плитка цвета вещи, с реальными фото подставится картинка.
export type Product = {
  id: string;
  title: string;
  brand: string;
  price: number;
  category: Category;
  color: ColorId;
  styles: StyleId[];
  department: 'men' | 'women' | 'unisex';
  image?: string;
  url: string;
};

type Seed = Omit<Product, 'url' | 'image'>;

const seeds: Seed[] = [
  // Верхняя одежда
  { id: 'jacket-leather', title: 'Кожаная куртка', brand: 'Monoline', price: 18900, category: 'outerwear', color: 'black', styles: ['minimal', 'street'], department: 'unisex' },
  { id: 'coat-wool', title: 'Шерстяное пальто', brand: 'Atelier 9', price: 24900, category: 'outerwear', color: 'gray', styles: ['classic', 'minimal'], department: 'unisex' },
  { id: 'trench', title: 'Тренч', brand: 'Atelier 9', price: 15900, category: 'outerwear', color: 'beige', styles: ['classic', 'vintage'], department: 'unisex' },
  { id: 'bomber', title: 'Бомбер', brand: 'Urban Roots', price: 8990, category: 'outerwear', color: 'green', styles: ['street', 'sport'], department: 'unisex' },
  { id: 'denim-jacket', title: 'Джинсовая куртка', brand: 'Nord', price: 7490, category: 'outerwear', color: 'blue', styles: ['casual', 'vintage'], department: 'unisex' },
  // Верх
  { id: 'hoodie', title: 'Худи оверсайз', brand: 'Urban Roots', price: 5490, category: 'top', color: 'gray', styles: ['street', 'casual'], department: 'unisex' },
  { id: 'tee-black', title: 'Футболка базовая', brand: 'Monoline', price: 1990, category: 'top', color: 'black', styles: ['minimal', 'casual'], department: 'unisex' },
  { id: 'tee-white', title: 'Футболка белая', brand: 'Monoline', price: 1990, category: 'top', color: 'white', styles: ['minimal', 'casual'], department: 'unisex' },
  { id: 'shirt-oxford', title: 'Рубашка оксфорд', brand: 'Nord', price: 4290, category: 'top', color: 'blue', styles: ['classic', 'casual'], department: 'unisex' },
  { id: 'knit', title: 'Свитер крупной вязки', brand: 'Kite', price: 6990, category: 'top', color: 'brown', styles: ['vintage', 'casual'], department: 'unisex' },
  { id: 'turtleneck', title: 'Водолазка', brand: 'Monoline', price: 3990, category: 'top', color: 'black', styles: ['minimal', 'classic'], department: 'unisex' },
  { id: 'longsleeve', title: 'Лонгслив для тренировок', brand: 'Slate', price: 3490, category: 'top', color: 'gray', styles: ['sport'], department: 'unisex' },
  { id: 'blouse', title: 'Шёлковая блуза', brand: 'Atelier 9', price: 5990, category: 'top', color: 'white', styles: ['classic', 'minimal'], department: 'women' },
  { id: 'cardigan', title: 'Кардиган', brand: 'Kite', price: 6490, category: 'top', color: 'beige', styles: ['vintage', 'casual'], department: 'women' },
  // Низ
  { id: 'jeans-straight', title: 'Джинсы прямые', brand: 'Nord', price: 5990, category: 'bottom', color: 'blue', styles: ['casual', 'street'], department: 'unisex' },
  { id: 'jeans-black', title: 'Чёрные джинсы', brand: 'Nord', price: 5990, category: 'bottom', color: 'black', styles: ['street', 'minimal'], department: 'unisex' },
  { id: 'trousers-wool', title: 'Брюки со стрелками', brand: 'Atelier 9', price: 7490, category: 'bottom', color: 'gray', styles: ['classic', 'minimal'], department: 'unisex' },
  { id: 'chinos', title: 'Брюки чинос', brand: 'Nord', price: 4990, category: 'bottom', color: 'beige', styles: ['casual', 'classic'], department: 'unisex' },
  { id: 'cargo', title: 'Брюки карго', brand: 'Urban Roots', price: 6290, category: 'bottom', color: 'green', styles: ['street', 'sport'], department: 'unisex' },
  { id: 'joggers', title: 'Джоггеры', brand: 'Slate', price: 3990, category: 'bottom', color: 'black', styles: ['sport', 'casual'], department: 'unisex' },
  { id: 'skirt-midi', title: 'Юбка миди', brand: 'Atelier 9', price: 5490, category: 'bottom', color: 'brown', styles: ['classic', 'vintage'], department: 'women' },
  { id: 'wide-trousers', title: 'Широкие брюки', brand: 'Monoline', price: 6990, category: 'bottom', color: 'black', styles: ['minimal', 'casual'], department: 'women' },
  // Обувь
  { id: 'sneakers-white', title: 'Кеды белые', brand: 'Slate', price: 7990, category: 'shoes', color: 'white', styles: ['casual', 'minimal'], department: 'unisex' },
  { id: 'boots', title: 'Ботинки челси', brand: 'Slate', price: 12900, category: 'shoes', color: 'black', styles: ['classic', 'vintage'], department: 'unisex' },
  { id: 'running', title: 'Кроссовки беговые', brand: 'Slate', price: 9490, category: 'shoes', color: 'gray', styles: ['sport', 'street'], department: 'unisex' },
  { id: 'chunky', title: 'Массивные кроссовки', brand: 'Urban Roots', price: 10900, category: 'shoes', color: 'black', styles: ['street'], department: 'unisex' },
  { id: 'derby', title: 'Дерби', brand: 'Slate', price: 11900, category: 'shoes', color: 'brown', styles: ['classic', 'vintage'], department: 'men' },
  { id: 'loafers', title: 'Лоферы', brand: 'Slate', price: 9900, category: 'shoes', color: 'brown', styles: ['classic', 'vintage'], department: 'women' },
];

export const catalog: Product[] = seeds.map((seed) => ({
  ...seed,
  url: `https://example.com/shop/${seed.id}?ref=look`,
}));

const BY_ID = new Map(catalog.map((product) => [product.id, product]));

export const productById = (id: string) => BY_ID.get(id);

// Мужское — мужское и унисекс, женское — женское и унисекс, «без разницы» — всё.
export const catalogFor = (department: Department): Product[] =>
  department === 'any'
    ? catalog
    : catalog.filter((product) => product.department === 'unisex' || product.department === department);

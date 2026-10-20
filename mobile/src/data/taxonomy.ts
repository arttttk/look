export type Category = 'outerwear' | 'top' | 'bottom' | 'shoes' | 'accessory';

export const categories: { id: Category; title: string; plural: string }[] = [
  { id: 'outerwear', title: 'Верхняя одежда', plural: 'Верхняя одежда' },
  { id: 'top', title: 'Верх', plural: 'Верх' },
  { id: 'bottom', title: 'Низ', plural: 'Низ' },
  { id: 'shoes', title: 'Обувь', plural: 'Обувь' },
  { id: 'accessory', title: 'Аксессуар', plural: 'Аксессуары' },
];

export const categoryTitle = (id: Category) => categories.find((category) => category.id === id)?.title ?? id;

export type ColorId = 'black' | 'white' | 'gray' | 'beige' | 'navy' | 'blue' | 'brown' | 'green' | 'red';

// neutral — базовые цвета, которые сочетаются почти со всем; акцентных в образе должно быть не больше одного.
export const colorOptions: { id: ColorId; title: string; hex: string; neutral: boolean }[] = [
  { id: 'black', title: 'Чёрный', hex: '#1F1F1F', neutral: true },
  { id: 'white', title: 'Белый', hex: '#EFEDE8', neutral: true },
  { id: 'gray', title: 'Серый', hex: '#9A9A9A', neutral: true },
  { id: 'beige', title: 'Бежевый', hex: '#CDB99A', neutral: true },
  { id: 'navy', title: 'Тёмно-синий', hex: '#222C47', neutral: true },
  { id: 'blue', title: 'Голубой', hex: '#4F74A8', neutral: true },
  { id: 'brown', title: 'Коричневый', hex: '#6B4A35', neutral: true },
  { id: 'green', title: 'Зелёный', hex: '#52704B', neutral: false },
  { id: 'red', title: 'Красный', hex: '#B23A3A', neutral: false },
];

const COLORS = new Map(colorOptions.map((color) => [color.id, color]));

export const colorById = (id: ColorId) => COLORS.get(id)!;

export const isCategory = (value: unknown): value is Category =>
  categories.some((category) => category.id === value);

export const isColorId = (value: unknown): value is ColorId => typeof value === 'string' && COLORS.has(value as ColorId);

// Для кого подбираем одежду.
export type Department = 'men' | 'women' | 'any';

export const departments: { id: Department; title: string; description: string }[] = [
  { id: 'men', title: 'Мужское', description: 'Мужская и унисекс-одежда' },
  { id: 'women', title: 'Женское', description: 'Женская и унисекс-одежда' },
  { id: 'any', title: 'Без разницы', description: 'Показывать всё подряд' },
];

export const isDepartment = (value: unknown): value is Department =>
  departments.some((department) => department.id === value);

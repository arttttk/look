import { photo } from './photo';

export type StyleId = 'minimal' | 'street' | 'classic' | 'casual' | 'sport' | 'vintage';

export type StyleOption = {
  id: StyleId;
  title: string;
  description: string;
  image: string;
  color: string;
};

export const styleOptions: StyleOption[] = [
  { id: 'minimal', title: 'Минимализм', description: 'Чистые линии и нейтральные цвета', image: photo('style-minimal', 480, 540), color: '#26252A' },
  { id: 'street', title: 'Стритвир', description: 'Свободный крой, худи и кроссовки', image: photo('style-street', 480, 540), color: '#2A2D2A' },
  { id: 'classic', title: 'Классика', description: 'Пальто, рубашки, строгие силуэты', image: photo('style-classic', 480, 540), color: '#2D2823' },
  { id: 'casual', title: 'Кэжуал', description: 'Удобно и просто на каждый день', image: photo('style-casual', 480, 540), color: '#2A2A2E' },
  { id: 'sport', title: 'Спорт', description: 'Функционально и динамично', image: photo('style-sport', 480, 540), color: '#232A2E' },
  { id: 'vintage', title: 'Винтаж', description: 'Образы из прошлых десятилетий', image: photo('style-vintage', 480, 540), color: '#33291F' },
];

const KNOWN_IDS = new Set<string>(styleOptions.map((option) => option.id));

export const isStyleId = (value: unknown): value is StyleId =>
  typeof value === 'string' && KNOWN_IDS.has(value);

export const styleTitle = (id: StyleId) => styleOptions.find((option) => option.id === id)?.title ?? id;

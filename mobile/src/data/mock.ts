// Промо-баннеры главной. Поле `image` — заглушка (picsum), позже заменяется на обложки с бэкенда;
// `color` — фон на время загрузки картинки и на случай, если она не загрузилась.
// Образы, ленту и каталог собирает lib/outfits — здесь их нет.
import { photo } from './photo';

export type Banner = {
  id: string;
  badge: string;
  title: string;
  image: string;
  color: string;
};

export const banners: Banner[] = [
  { id: 'b1', badge: 'Сезон осень 2026', title: 'Лучшие рекомендации', image: photo('look-b1', 640, 320), color: '#2A2724' },
  { id: 'b2', badge: 'Винтаж 2026', title: 'Осень', image: photo('look-b2', 640, 320), color: '#3A302A' },
  { id: 'b3', badge: 'Тренд недели', title: 'Оверсайз и слои', image: photo('look-b3', 640, 320), color: '#262A2D' },
  { id: 'b4', badge: 'Новинки', title: 'Тёплые оттенки', image: photo('look-b4', 640, 320), color: '#3B2C25' },
];

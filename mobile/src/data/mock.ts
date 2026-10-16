export type Look = {
  id: string;
  title: string;
  tag: string;
  color: string;
  pieces: string[];
};

export type QuickAction = {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
};

export const lookOfTheDay: Look = {
  id: 'today',
  title: 'Городской минимализм',
  tag: 'Образ дня · 18°C, облачно',
  color: '#2B2A28',
  pieces: ['🧥', '👕', '👖', '👟'],
};

export const quickActions: QuickAction[] = [
  { id: 'scan', title: 'Добавить вещь', subtitle: 'Сфотографировать', icon: '📸' },
  { id: 'wardrobe', title: 'Мой гардероб', subtitle: '0 вещей', icon: '👚' },
  { id: 'tryon', title: 'Примерить', subtitle: 'Скоро', icon: '✨' },
];

export const recommendations: Look[] = [
  { id: 'r1', title: 'Офис без галстука', tag: 'Работа', color: '#D9C7B0', pieces: ['🧥', '👔', '👖'] },
  { id: 'r2', title: 'Выходные в парке', tag: 'Casual', color: '#BFD3C1', pieces: ['🧢', '👕', '👟'] },
  { id: 'r3', title: 'Вечер в городе', tag: 'Свидание', color: '#E4B7AC', pieces: ['👗', '👜', '👠'] },
  { id: 'r4', title: 'Спорт и прогулка', tag: 'Актив', color: '#B7C6DD', pieces: ['🧥', '🩳', '👟'] },
];

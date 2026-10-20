// Картинки-заглушки (picsum). Когда появятся реальные фото, меняется только эта функция.
export const photo = (seed: string, width: number, height: number) =>
  `https://picsum.photos/seed/${seed}/${width}/${height}`;

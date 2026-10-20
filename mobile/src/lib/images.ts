import { Platform } from 'react-native';

// Фото вещи из камеры/галереи лежит во временной папке и может быть удалено системой —
// копируем в постоянное хранилище приложения. На вебе файловой системы нет, оставляем как есть.
export async function persistImage(uri: string): Promise<string> {
  if (Platform.OS === 'web') return uri;

  const { Directory, File, Paths } = await import('expo-file-system');

  const source = new File(uri);
  const directory = new Directory(Paths.document, 'wardrobe');
  directory.create({ idempotent: true });

  const target = new File(directory, `${Date.now().toString(36)}${source.extension || '.jpg'}`);
  await source.copy(target);
  return target.uri;
}

export function removeImage(uri: string) {
  if (Platform.OS === 'web') return;

  import('expo-file-system')
    .then(({ File }) => {
      const file = new File(uri);
      if (file.exists) file.delete();
    })
    .catch(() => {
      // Файла уже нет или он недоступен — удалять нечего.
    });
}

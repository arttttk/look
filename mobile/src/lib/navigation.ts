import { router } from 'expo-router';

// Закрыть экран; если истории нет (открыт по ссылке) — вернуться на главную.
export function closeScreen() {
  if (router.canGoBack()) router.back();
  else router.replace('/');
}

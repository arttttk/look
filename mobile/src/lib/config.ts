import Constants from 'expo-constants';
import { Platform } from 'react-native';

const API_PORT = 8000;

// Адрес бэкенда. Порядок: переменная EXPO_PUBLIC_API_URL → тот же компьютер, с которого
// раздаётся приложение (Expo Go на телефоне, веб в браузере) → localhost.
export function resolveApiUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv) return fromEnv.replace(/\/$/, '');

  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    return `http://${window.location.hostname}:${API_PORT}`;
  }

  const host = Constants.expoConfig?.hostUri?.split(':')[0];
  return `http://${host ?? 'localhost'}:${API_PORT}`;
}

export const API_URL = resolveApiUrl();

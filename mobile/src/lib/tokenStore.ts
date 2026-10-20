import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const KEY = 'look.session-token';

// Токен — это ключ к данным пользователя, поэтому на телефоне он лежит в защищённом хранилище
// (Keychain / Keystore). На вебе защищённого хранилища нет — используем обычное.
const useSecureStore = Platform.OS !== 'web';

export async function readToken(): Promise<string | null> {
  try {
    return useSecureStore ? await SecureStore.getItemAsync(KEY) : await AsyncStorage.getItem(KEY);
  } catch {
    return null;
  }
}

export async function saveToken(token: string): Promise<void> {
  if (useSecureStore) await SecureStore.setItemAsync(KEY, token);
  else await AsyncStorage.setItem(KEY, token);
}

export async function clearToken(): Promise<void> {
  try {
    if (useSecureStore) await SecureStore.deleteItemAsync(KEY);
    else await AsyncStorage.removeItem(KEY);
  } catch {
    // Нечего удалять или хранилище недоступно — токен всё равно забыт в памяти.
  }
}

import * as Location from 'expo-location';

import { type City, type Location as ProfileLocation } from '@/data/profile';
import { api } from '@/lib/api';

export const searchCities = (query: string) => api.get<City[]>('/geo/cities', { q: query });

// Геопозицию получить не удалось (нет разрешения, нет сигнала, веб без геокодера): человеку
// остаётся выбрать город из списка — текст ошибки ему и показываем.
export class LocationUnavailable extends Error {}

export async function detectLocation(): Promise<ProfileLocation> {
  try {
    const permission = await Location.requestForegroundPermissionsAsync();
    if (!permission.granted) {
      throw new LocationUnavailable('Нет доступа к геопозиции. Выберите город из списка.');
    }

    const position = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    const [address] = await Location.reverseGeocodeAsync(position.coords);
    const city = address?.city ?? address?.subregion ?? address?.region;
    const country = address?.isoCountryCode;
    if (!city || !country) throw new LocationUnavailable('Не удалось определить город. Выберите его из списка.');

    return {
      city,
      country_code: country,
      lat: position.coords.latitude,
      lon: position.coords.longitude,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone ?? null,
    };
  } catch (failure) {
    if (failure instanceof LocationUnavailable) throw failure;
    throw new LocationUnavailable('Не удалось определить место автоматически. Выберите город из списка.');
  }
}

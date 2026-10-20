import type { StyleId } from '@/data/styles';
import type { Department } from '@/data/taxonomy';

// Формы данных — как их отдаёт и принимает бэкенд (backend/app/api/schemas.py).

export type Budget = 'low' | 'mid' | 'high';

export type Location = {
  city: string;
  country_code: string;
  lat: number;
  lon: number;
  timezone: string | null;
};

export type Profile = {
  id: string;
  phone: string | null;
  email: string | null;
  name: string | null;
  birth_year: number | null;
  onboarded: boolean;
  department: Department;
  // Пустой список — «не определился»: бэкенд тогда подсказывает стиль региона.
  styles: StyleId[];
  budget: Budget | null;
  location: Location | null;
  regional_styles: StyleId[];
};

// Что можно менять через PATCH /me. null очищает необязательные поля.
export type ProfilePatch = Partial<
  Pick<Profile, 'name' | 'birth_year' | 'onboarded' | 'department' | 'styles' | 'budget' | 'location'>
>;

export const EMPTY_PROFILE: Profile = {
  id: '',
  phone: null,
  email: null,
  name: null,
  birth_year: null,
  onboarded: false,
  department: 'any',
  styles: [],
  budget: null,
  location: null,
  regional_styles: [],
};

export const budgetOptions: { id: Budget; title: string; description: string }[] = [
  { id: 'low', title: 'Эконом', description: 'До 15 000 ₽ за образ' },
  { id: 'mid', title: 'Средний', description: 'До 30 000 ₽ за образ' },
  { id: 'high', title: 'Без ограничений', description: 'Цена не главное' },
];

export const budgetTitle = (id: Budget | null) => budgetOptions.find((option) => option.id === id)?.title ?? 'Не указан';

export type City = {
  city: string;
  region: string | null;
  country: string | null;
  country_code: string;
  lat: number;
  lon: number;
  timezone: string | null;
};

export type Weather = {
  city: string;
  temperature_c: number;
  feels_like_c: number;
  condition: 'clear' | 'cloudy' | 'fog' | 'rain' | 'snow' | 'storm';
  label: string;
  is_day: boolean;
  precipitation_mm: number;
  wind_kmh: number;
  observed_at: string;
};

export type CodeSent = {
  kind: 'phone' | 'email';
  identifier: string;
  resend_after: number;
  dev_code: string | null;
};

export type TokenResponse = {
  access_token: string;
  user_id: string;
  is_new: boolean;
};

export const locationFromCity = (city: City): Location => ({
  city: city.city,
  country_code: city.country_code,
  lat: city.lat,
  lon: city.lon,
  timezone: city.timezone,
});

export const locationTitle = (location: Location | null) => (location ? location.city : 'Не указан');

// «18°C, облачно» — подпись под образом дня.
export const weatherLabel = (weather: Weather) => `${Math.round(weather.temperature_c)}°C, ${weather.label}`;

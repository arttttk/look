export const MAX_NAME_LENGTH = 40;
const MIN_BIRTH_YEAR = 1930;
const MIN_AGE = 10;

// Год рождения из поля ввода: пусто — «не указан», мусор или неправдоподобный год — undefined.
export function parseBirthYear(text: string, currentYear = new Date().getFullYear()): number | null | undefined {
  const value = text.trim();
  if (value === '') return null;
  if (!/^\d{4}$/.test(value)) return undefined;

  const year = Number(value);
  return year >= MIN_BIRTH_YEAR && year <= currentYear - MIN_AGE ? year : undefined;
}

export const cleanName = (text: string) => text.trim().replace(/\s+/g, ' ');

export function validateName(text: string): string | null {
  return cleanName(text).length > MAX_NAME_LENGTH ? `Имя не длиннее ${MAX_NAME_LENGTH} символов` : null;
}

// Телефон и почта различаются по «@»; нормализацию (8 999… → +7 999…) делает сервер.
export const looksLikeEmail = (text: string) => text.includes('@');

export function describeContact(phone: string | null, email: string | null) {
  return phone ?? email ?? '';
}

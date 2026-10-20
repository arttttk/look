// 18900 -> «18 900 ₽» (неразрывные пробелы, чтобы цена не переносилась)
export function formatPrice(price: number) {
  return `${String(price).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')} ₽`;
}

// plural(3, ['вещь', 'вещи', 'вещей']) -> 'вещи'
export function plural(count: number, forms: [one: string, few: string, many: string]) {
  const n = Math.abs(count) % 100;
  const last = n % 10;
  if (n > 10 && n < 20) return forms[2];
  if (last > 1 && last < 5) return forms[1];
  if (last === 1) return forms[0];
  return forms[2];
}

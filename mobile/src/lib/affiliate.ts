import * as WebBrowser from 'expo-web-browser';

import type { Product } from '@/data/catalog';

// Единственная точка выхода по партнёрским ссылкам. Сюда позже добавятся
// маркировка рекламы (ERID) и учёт кликов через бэкенд-редирект.
export async function openProduct(product: Product) {
  await WebBrowser.openBrowserAsync(product.url);
}

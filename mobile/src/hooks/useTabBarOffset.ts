import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { spacing } from '@/theme';

// Расстояние от нижнего края экрана до плавающего таб-бара.
export function useTabBarOffset() {
  const { bottom } = useSafeAreaInsets();
  return Math.max(bottom, spacing.sm);
}

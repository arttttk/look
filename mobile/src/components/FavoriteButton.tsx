import { Pressable, type StyleProp, StyleSheet, type ViewStyle } from 'react-native';

import { Icon } from '@/components/Icon';
import { useFavorites } from '@/state/favorites';
import { colors } from '@/theme';

type Props = {
  outfitId: string;
  size?: number;
  style?: StyleProp<ViewStyle>;
};

export function FavoriteButton({ outfitId, size = 22, style }: Props) {
  const { isFavorite, toggle } = useFavorites();
  const active = isFavorite(outfitId);

  return (
    <Pressable
      onPress={() => toggle(outfitId)}
      hitSlop={10}
      style={[styles.button, style]}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      accessibilityLabel={active ? 'Убрать из избранного' : 'В избранное'}>
      <Icon name="heart" size={size} color={active ? colors.like : colors.ink} filled={active} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});

import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Pressable, StyleSheet, Text } from 'react-native';

import { LookCollage } from '@/components/LookCollage';
import type { Outfit } from '@/lib/outfits';
import { colors, radius, spacing } from '@/theme';

type Props = {
  tag: string;
  outfit: Outfit;
  width: number;
};

// Компактная карточка для горизонтальной карусели на главной.
export function OutfitTile({ tag, outfit, width }: Props) {
  return (
    <Pressable
      onPress={() => router.push({ pathname: '/look/[id]', params: { id: outfit.id } })}
      style={({ pressed }) => [styles.card, { width }, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${outfit.title}, ${tag}`}>
      <LookCollage pieces={outfit.pieces} labels={false} style={StyleSheet.absoluteFill} />
      <LinearGradient
        colors={['rgba(0,0,0,0)', 'rgba(0,0,0,0.78)']}
        locations={[0.2, 1]}
        style={StyleSheet.absoluteFill}
      />
      <Text style={styles.tag}>{tag}</Text>
      <Text style={styles.title} numberOfLines={2}>
        {outfit.title}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    aspectRatio: 1.1,
    borderRadius: radius.md,
    overflow: 'hidden',
    padding: spacing.sm + 2,
    justifyContent: 'flex-end',
  },
  pressed: {
    opacity: 0.85,
  },
  tag: {
    fontSize: 11,
    fontWeight: '500',
    color: colors.onDarkSoft,
    marginBottom: 2,
  },
  title: {
    fontSize: 14,
    fontWeight: '800',
    lineHeight: 17,
    color: colors.onDark,
  },
});

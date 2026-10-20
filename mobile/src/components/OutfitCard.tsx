import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { FavoriteButton } from '@/components/FavoriteButton';
import { LookCollage } from '@/components/LookCollage';
import type { Outfit } from '@/lib/outfits';
import { colors, radius, spacing } from '@/theme';

type Props = {
  outfit: Outfit;
  width: number;
  subtitle?: string;
};

// Карточка образа для сеток (вкладка «Образы», «Все рекомендации»).
export function OutfitCard({ outfit, width, subtitle }: Props) {
  return (
    <View style={{ width }}>
      <Pressable
        onPress={() => router.push({ pathname: '/look/[id]', params: { id: outfit.id } })}
        style={({ pressed }) => pressed && styles.pressed}
        accessibilityRole="button"
        accessibilityLabel={outfit.title}>
        <LookCollage pieces={outfit.pieces} labels={false} style={styles.collage} />
        <Text style={styles.title} numberOfLines={2}>
          {outfit.title}
        </Text>
        {subtitle ? (
          <Text style={styles.subtitle} numberOfLines={2}>
            {subtitle}
          </Text>
        ) : null}
      </Pressable>
      <View style={styles.heart}>
        <FavoriteButton outfitId={outfit.id} size={18} style={styles.heartButton} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  pressed: {
    opacity: 0.85,
  },
  collage: {
    aspectRatio: 1,
    borderRadius: radius.md,
    marginBottom: spacing.sm,
  },
  title: {
    fontSize: 15,
    fontWeight: '800',
    color: colors.ink,
  },
  subtitle: {
    fontSize: 12,
    color: colors.inkSoft,
    marginTop: 2,
  },
  heart: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
  },
  heartButton: {
    width: 32,
    height: 32,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(255,255,255,0.85)',
  },
});

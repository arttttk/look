import { router } from 'expo-router';
import { memo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { FavoriteButton } from '@/components/FavoriteButton';
import { Icon } from '@/components/Icon';
import { LookCollage } from '@/components/LookCollage';
import { ProductRow } from '@/components/ProductRow';
import { styleTitle } from '@/data/styles';
import { formatPrice } from '@/lib/format';
import { type Outfit, piecesToBuy } from '@/lib/outfits';
import { colors, radius, spacing } from '@/theme';

type Props = {
  outfit: Outfit;
};

// Пост ленты: автоподобранный образ из каталога. Автора нет — образы собирает Look.
function OutfitPostCardBase({ outfit }: Props) {
  const toBuy = piecesToBuy(outfit);
  const products = toBuy.flatMap((piece) => piece.product ?? []);
  const total = products.reduce((sum, product) => sum + product.price, 0);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>L</Text>
        </View>
        <Text style={styles.name}>Подборка Look</Text>
        {outfit.styles.length > 0 ? <Text style={styles.role}>· {styleTitle(outfit.styles[0])}</Text> : null}
        <View style={styles.spacer} />
        <Icon name="ellipsis" size={22} color={colors.inkSoft} strokeWidth={3} />
      </View>

      <Text style={styles.caption}>{outfit.title}</Text>

      <Pressable
        onPress={() => router.push({ pathname: '/look/[id]', params: { id: outfit.id } })}
        accessibilityRole="button"
        accessibilityLabel={`Открыть образ: ${outfit.title}`}>
        <LookCollage pieces={outfit.pieces} style={styles.collage} />
      </Pressable>

      <View style={styles.actions}>
        <FavoriteButton outfitId={outfit.id} />
        <Text style={styles.total}>Весь образ · {formatPrice(total)}</Text>
      </View>

      <ProductRow products={products} />
    </View>
  );
}

export const OutfitPostCard = memo(OutfitPostCardBase);

const styles = StyleSheet.create({
  card: {
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.line,
    padding: spacing.md - 2,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.md - 2,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.onDark,
  },
  name: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.ink,
  },
  role: {
    fontSize: 13,
    color: colors.inkSoft,
  },
  spacer: {
    flex: 1,
  },
  caption: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.ink,
    marginBottom: spacing.md - 2,
  },
  collage: {
    aspectRatio: 1,
    borderRadius: radius.md,
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.md - 2,
  },
  total: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.ink,
  },
});

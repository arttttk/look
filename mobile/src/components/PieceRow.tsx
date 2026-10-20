import { Image } from 'expo-image';
import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { categoryTitle, colorById } from '@/data/taxonomy';
import { openProduct } from '@/lib/affiliate';
import { formatPrice } from '@/lib/format';
import type { Piece } from '@/lib/outfits';
import { colors, radius, spacing } from '@/theme';

// Строка вещи в составе образа: своя — ведёт в гардероб, из каталога — на покупку.
export function PieceRow({ piece }: { piece: Piece }) {
  const color = colorById(piece.color);
  const { product } = piece;

  const body = (
    <>
      <View style={[styles.thumb, { backgroundColor: color.hex }]}>
        {piece.image ? (
          <Image source={piece.image} contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
        ) : null}
      </View>
      <View style={styles.info}>
        <Text style={styles.category}>{categoryTitle(piece.category)}</Text>
        <Text style={styles.title} numberOfLines={2}>
          {piece.title}
        </Text>
        <Text style={styles.sub} numberOfLines={1}>
          {product ? `${product.brand} · ${color.title}` : color.title}
        </Text>
      </View>
    </>
  );

  if (product) {
    return (
      <View style={styles.row}>
        {body}
        <Pressable
          onPress={() => void openProduct(product)}
          style={({ pressed }) => [styles.buy, pressed && styles.pressed]}
          accessibilityRole="link"
          accessibilityLabel={`Купить: ${product.title}, ${formatPrice(product.price)}`}>
          <Text style={styles.buyText}>{formatPrice(product.price)}</Text>
          <Icon name="arrow-right" size={14} color={colors.onDark} />
        </Pressable>
      </View>
    );
  }

  return (
    <Pressable
      onPress={() => router.push({ pathname: '/item/[id]', params: { id: piece.id.slice(2) } })}
      style={({ pressed }) => [styles.row, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${piece.title}. Из вашего гардероба`}>
      {body}
      <View style={styles.own}>
        <Icon name="check" size={14} color={colors.ink} strokeWidth={2.5} />
        <Text style={styles.ownText}>В гардеробе</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 2,
    padding: spacing.sm + 2,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
  },
  pressed: {
    opacity: 0.75,
  },
  thumb: {
    width: 56,
    height: 70,
    borderRadius: radius.sm - 2,
    overflow: 'hidden',
  },
  info: {
    flex: 1,
    gap: 2,
  },
  category: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    color: colors.inkSoft,
  },
  title: {
    fontSize: 15,
    fontWeight: '800',
    color: colors.ink,
  },
  sub: {
    fontSize: 12,
    color: colors.inkSoft,
  },
  buy: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs + 2,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md - 2,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
  },
  buyText: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.onDark,
  },
  own: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm + 2,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
  },
  ownText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.ink,
  },
});

import { Image } from 'expo-image';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import type { Product } from '@/data/catalog';
import { colorById } from '@/data/taxonomy';
import { openProduct } from '@/lib/affiliate';
import { formatPrice } from '@/lib/format';
import { colors, radius, spacing } from '@/theme';

type Props = {
  products: Product[];
  heading?: string;
};

export function ProductRow({ products, heading = 'Вещи из образа' }: Props) {
  if (products.length === 0) return null;

  return (
    <View style={styles.wrap}>
      <Text style={styles.heading}>{heading}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.list}>
        {products.map((product) => (
          <Pressable
            key={product.id}
            onPress={() => void openProduct(product)}
            style={({ pressed }) => [styles.item, pressed && styles.pressed]}
            accessibilityRole="link"
            accessibilityLabel={`${product.title}, ${product.brand}, ${formatPrice(product.price)}. Купить`}>
            <View style={[styles.thumb, { backgroundColor: colorById(product.color).hex }]}>
              {product.image ? (
                <Image source={product.image} contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
              ) : null}
            </View>
            <View style={styles.info}>
              <Text style={styles.brand} numberOfLines={1}>
                {product.brand}
              </Text>
              <Text style={styles.title} numberOfLines={2}>
                {product.title}
              </Text>
              <View style={styles.buy}>
                <Text style={styles.price}>{formatPrice(product.price)}</Text>
                <Icon name="arrow-right" size={14} color={colors.ink} />
              </View>
            </View>
          </Pressable>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginTop: spacing.md - 2,
  },
  heading: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.inkSoft,
    marginBottom: spacing.sm,
  },
  list: {
    gap: spacing.sm,
  },
  item: {
    flexDirection: 'row',
    gap: spacing.sm + 2,
    width: 220,
    padding: spacing.sm,
    backgroundColor: colors.bg,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
  },
  pressed: {
    opacity: 0.7,
  },
  thumb: {
    width: 56,
    height: 70,
    borderRadius: radius.sm - 2,
    overflow: 'hidden',
  },
  info: {
    flex: 1,
    justifyContent: 'space-between',
  },
  brand: {
    fontSize: 11,
    color: colors.inkSoft,
  },
  title: {
    fontSize: 13,
    fontWeight: '700',
    lineHeight: 16,
    color: colors.ink,
  },
  buy: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  price: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.ink,
  },
});

import { useLocalSearchParams } from 'expo-router';
import { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { EmptyState } from '@/components/EmptyState';
import { FavoriteButton } from '@/components/FavoriteButton';
import { LookCollage } from '@/components/LookCollage';
import { PieceRow } from '@/components/PieceRow';
import { ScreenHeader } from '@/components/ScreenHeader';
import { styleTitle } from '@/data/styles';
import { formatPrice, plural } from '@/lib/format';
import { closeScreen } from '@/lib/navigation';
import { piecesToBuy, resolveOutfit } from '@/lib/outfits';
import { useProfile } from '@/state/profile';
import { useWardrobe } from '@/state/wardrobe';
import { colors, radius, spacing } from '@/theme';

export default function LookScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { profile } = useProfile();
  const { ready, items } = useWardrobe();

  const outfit = useMemo(
    () => (ready ? resolveOutfit(id, items, profile.styles) : null),
    [ready, id, items, profile.styles],
  );

  if (!ready) return <SafeAreaView style={styles.safe} />;

  if (!outfit) {
    return (
      <SafeAreaView style={styles.safe}>
        <ScreenHeader />
        <EmptyState
          icon="heart"
          title="Образ не найден"
          text="Возможно, одной из вещей уже нет в гардеробе."
          actionLabel="Вернуться"
          onAction={closeScreen}
        />
      </SafeAreaView>
    );
  }

  const toBuy = piecesToBuy(outfit);
  const own = outfit.pieces.length - toBuy.length;
  const total = toBuy.reduce((sum, piece) => sum + (piece.product?.price ?? 0), 0);

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <ScreenHeader right={<FavoriteButton outfitId={outfit.id} size={20} style={styles.heart} />} />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <LookCollage pieces={outfit.pieces} style={styles.collage} />

        <Text style={styles.title}>{outfit.title}</Text>
        {outfit.styles.length > 0 ? (
          <View style={styles.chips}>
            {outfit.styles.map((style) => (
              <View key={style} style={styles.chip}>
                <Text style={styles.chipText}>{styleTitle(style)}</Text>
              </View>
            ))}
          </View>
        ) : null}

        <Text style={styles.heading}>Из чего состоит</Text>
        <View style={styles.list}>
          {outfit.pieces.map((piece) => (
            <PieceRow key={piece.id} piece={piece} />
          ))}
        </View>

        {toBuy.length > 0 ? (
          <View style={styles.summary}>
            <Text style={styles.summaryTitle}>
              {own > 0
                ? `Докупить ${toBuy.length} ${plural(toBuy.length, ['вещь', 'вещи', 'вещей'])} · ${formatPrice(total)}`
                : `Весь образ · ${formatPrice(total)}`}
            </Text>
            <Text style={styles.summaryText}>Цены и наличие уточняйте на сайте магазина — по кнопке «Купить».</Text>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  heart: {
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
  },
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  collage: {
    aspectRatio: 1,
    borderRadius: radius.lg,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    lineHeight: 32,
    color: colors.ink,
    marginTop: spacing.md,
  },
  chips: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.sm + 2,
  },
  chip: {
    paddingVertical: spacing.xs + 2,
    paddingHorizontal: spacing.md - 2,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.ink,
  },
  heading: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.ink,
    marginTop: spacing.lg,
    marginBottom: spacing.md - 2,
  },
  list: {
    gap: spacing.sm,
  },
  summary: {
    marginTop: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.chip,
    gap: spacing.xs,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.ink,
  },
  summaryText: {
    fontSize: 12,
    lineHeight: 17,
    color: colors.inkSoft,
  },
});

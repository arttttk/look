import { useMemo } from 'react';
import { FlatList, StyleSheet, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { OutfitCard } from '@/components/OutfitCard';
import { ScreenHeader } from '@/components/ScreenHeader';
import { describeOutfit, generateFeedOutfits } from '@/lib/outfits';
import { useProfile } from '@/state/profile';
import { colors, spacing } from '@/theme';

export default function RecommendationsScreen() {
  const { width } = useWindowDimensions();
  const { profile } = useProfile();

  const outfits = useMemo(
    () => generateFeedOutfits(profile.department, profile.styles),
    [profile.department, profile.styles],
  );
  const cardWidth = Math.floor((width - spacing.md * 2 - spacing.sm) / 2);

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <ScreenHeader title="Рекомендации для вас" />
      <FlatList
        data={outfits}
        keyExtractor={(outfit) => outfit.id}
        numColumns={2}
        renderItem={({ item }) => <OutfitCard outfit={item} width={cardWidth} subtitle={describeOutfit(item)} />}
        columnWrapperStyle={styles.row}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.list}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  list: {
    padding: spacing.md,
  },
  row: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
});

import { router } from 'expo-router';
import { useMemo, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { EmptyState } from '@/components/EmptyState';
import { OutfitCard } from '@/components/OutfitCard';
import { ProductRow } from '@/components/ProductRow';
import { categoryTitle } from '@/data/taxonomy';
import { useTabBarOffset } from '@/hooks/useTabBarOffset';
import { plural } from '@/lib/format';
import {
  describeOutfit,
  generateWardrobeOutfits,
  missingCategories,
  resolveOutfit,
  suggestProducts,
} from '@/lib/outfits';
import { useFavorites } from '@/state/favorites';
import { useProfile } from '@/state/profile';
import { useWardrobe } from '@/state/wardrobe';
import { colors, layout, radius, spacing } from '@/theme';

type Tab = 'wardrobe' | 'favorites';

export default function LooksScreen() {
  const { width } = useWindowDimensions();
  const tabBarOffset = useTabBarOffset();
  const { profile } = useProfile();
  const { ready, items } = useWardrobe();
  const { ids } = useFavorites();
  const [tab, setTab] = useState<Tab>('wardrobe');

  const generated = useMemo(
    () => generateWardrobeOutfits(items, profile.department, profile.styles),
    [items, profile.department, profile.styles],
  );
  const saved = useMemo(
    () => ids.flatMap((id) => resolveOutfit(id, items, profile.styles) ?? []),
    [ids, items, profile.styles],
  );
  const missing = useMemo(() => missingCategories(items), [items]);

  if (!ready) return <SafeAreaView style={styles.safe} />;

  const cardWidth = Math.floor((width - spacing.md * 2 - spacing.sm) / 2);
  const data = tab === 'wardrobe' ? generated : saved;

  const header = (
    <View>
      <Text style={styles.title}>Образы</Text>
      <View style={styles.segments}>
        <Segment label="Из гардероба" active={tab === 'wardrobe'} onPress={() => setTab('wardrobe')} />
        <Segment label={`Избранное · ${saved.length}`} active={tab === 'favorites'} onPress={() => setTab('favorites')} />
      </View>
      {tab === 'wardrobe' && generated.length > 0 ? (
        <Text style={styles.count}>
          Собрано {generated.length} {plural(generated.length, ['образ', 'образа', 'образов'])}
        </Text>
      ) : null}
    </View>
  );

  const footer =
    tab === 'wardrobe' && items.length > 0 && missing.length > 0 ? (
      <View style={styles.missing}>
        <Text style={styles.missingTitle}>Чего не хватает</Text>
        <Text style={styles.missingText}>
          Чтобы образы собирались полностью из ваших вещей, добавьте их в гардероб или докупите.
        </Text>
        {missing.map((category) => (
          <ProductRow
            key={category}
            heading={`Не хватает: ${categoryTitle(category).toLowerCase()}`}
            products={suggestProducts(category, profile.department, profile.styles)}
          />
        ))}
      </View>
    ) : null;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <FlatList
        data={data}
        keyExtractor={(outfit) => outfit.id}
        numColumns={2}
        renderItem={({ item }) => <OutfitCard outfit={item} width={cardWidth} subtitle={describeOutfit(item)} />}
        columnWrapperStyle={styles.row}
        ListHeaderComponent={header}
        ListFooterComponent={footer}
        ListEmptyComponent={
          tab === 'wardrobe' ? (
            <EmptyState
              icon="shirt"
              title="Сначала добавьте вещи"
              text="Сфотографируйте несколько вещей из гардероба — мы соберём из них образы."
              actionLabel="Добавить вещь"
              onAction={() => router.push('/add-item')}
            />
          ) : (
            <EmptyState
              icon="heart"
              title="Пока ничего не сохранено"
              text="Нажимайте на сердечко у понравившегося образа — он появится здесь."
            />
          )
        }
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.list, { paddingBottom: tabBarOffset + layout.tabBarHeight + spacing.md }]}
      />
    </SafeAreaView>
  );
}

function Segment({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.segment, active && styles.segmentActive]}
      accessibilityRole="tab"
      accessibilityState={{ selected: active }}>
      <Text style={[styles.segmentText, active && styles.segmentTextActive]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  list: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    flexGrow: 1,
  },
  row: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.ink,
  },
  segments: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.md,
    marginBottom: spacing.md,
  },
  segment: {
    paddingVertical: spacing.sm + 1,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
  },
  segmentActive: {
    backgroundColor: colors.ink,
  },
  segmentText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.ink,
  },
  segmentTextActive: {
    color: colors.onDark,
  },
  count: {
    fontSize: 13,
    color: colors.inkSoft,
    marginBottom: spacing.md,
  },
  missing: {
    marginTop: spacing.sm,
    padding: spacing.md,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
  },
  missingTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.ink,
  },
  missingText: {
    fontSize: 13,
    lineHeight: 18,
    color: colors.inkSoft,
    marginTop: spacing.xs,
  },
});

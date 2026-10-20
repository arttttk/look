import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useState } from 'react';
import { FlatList, Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { EmptyState } from '@/components/EmptyState';
import { Icon } from '@/components/Icon';
import { type Category, categories, colorById } from '@/data/taxonomy';
import { itemLabel, type WardrobeItem } from '@/data/wardrobe';
import { useTabBarOffset } from '@/hooks/useTabBarOffset';
import { plural } from '@/lib/format';
import { useWardrobe } from '@/state/wardrobe';
import { colors, layout, radius, spacing } from '@/theme';

const COLUMNS = 3;

export default function WardrobeScreen() {
  const { width } = useWindowDimensions();
  const tabBarOffset = useTabBarOffset();
  const { ready, items } = useWardrobe();
  const [filter, setFilter] = useState<Category | 'all'>('all');

  if (!ready) return <SafeAreaView style={styles.safe} />;

  const tileWidth = Math.floor((width - spacing.md * 2 - spacing.sm * (COLUMNS - 1)) / COLUMNS);
  const visible = filter === 'all' ? items : items.filter((item) => item.category === filter);
  const countIn = (category: Category) => items.filter((item) => item.category === category).length;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Гардероб</Text>
          <Text style={styles.count}>
            {items.length} {plural(items.length, ['вещь', 'вещи', 'вещей'])}
          </Text>
        </View>
        <Pressable
          onPress={() => router.push('/add-item')}
          style={({ pressed }) => [styles.add, pressed && styles.pressed]}
          accessibilityRole="button"
          accessibilityLabel="Добавить вещь">
          <Icon name="plus" size={22} color={colors.onDark} strokeWidth={2.25} />
        </Pressable>
      </View>

      {items.length > 0 ? (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.chipsScroll}
          contentContainerStyle={styles.chips}>
          <Chip label={`Все · ${items.length}`} active={filter === 'all'} onPress={() => setFilter('all')} />
          {categories
            .filter((category) => countIn(category.id) > 0)
            .map((category) => (
              <Chip
                key={category.id}
                label={`${category.plural} · ${countIn(category.id)}`}
                active={filter === category.id}
                onPress={() => setFilter(category.id)}
              />
            ))}
        </ScrollView>
      ) : null}

      <FlatList
        data={visible}
        keyExtractor={(item) => item.id}
        numColumns={COLUMNS}
        renderItem={({ item }) => <ItemTile item={item} width={tileWidth} />}
        columnWrapperStyle={styles.row}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.list, { paddingBottom: tabBarOffset + layout.tabBarHeight + spacing.md }]}
        ListEmptyComponent={
          items.length === 0 ? (
            <EmptyState
              icon="shirt"
              title="Гардероб пока пуст"
              text="Сфотографируйте свои вещи — мы соберём из них образы и подскажем, что докупить."
              actionLabel="Добавить вещь"
              onAction={() => router.push('/add-item')}
            />
          ) : (
            <EmptyState icon="shirt" title="В этой категории пусто" text="Выберите другую категорию или добавьте вещь." />
          )
        }
      />
    </SafeAreaView>
  );
}

function Chip({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, active && styles.chipActive]}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}>
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </Pressable>
  );
}

function ItemTile({ item, width }: { item: WardrobeItem; width: number }) {
  return (
    <Pressable
      onPress={() => router.push({ pathname: '/item/[id]', params: { id: item.id } })}
      style={({ pressed }) => [{ width }, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={itemLabel(item)}>
      <View style={[styles.photo, { backgroundColor: colorById(item.color).hex }]}>
        <Image source={item.image} contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
        <View style={[styles.dot, { backgroundColor: colorById(item.color).hex }]} />
      </View>
      <Text style={styles.label} numberOfLines={1}>
        {itemLabel(item)}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.ink,
  },
  count: {
    fontSize: 14,
    color: colors.inkSoft,
    marginTop: 2,
  },
  add: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: {
    opacity: 0.8,
  },
  chipsScroll: {
    flexGrow: 0,
  },
  chips: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  chip: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md - 2,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
  },
  chipActive: {
    backgroundColor: colors.ink,
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.ink,
  },
  chipTextActive: {
    color: colors.onDark,
  },
  list: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    flexGrow: 1,
  },
  row: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  photo: {
    aspectRatio: 0.8,
    borderRadius: radius.md,
    overflow: 'hidden',
    marginBottom: spacing.xs,
  },
  dot: {
    position: 'absolute',
    left: spacing.sm,
    bottom: spacing.sm,
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: colors.onDark,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.ink,
  },
});

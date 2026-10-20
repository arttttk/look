import { router } from 'expo-router';
import { useMemo } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BannerCard } from '@/components/BannerCard';
import { HeroCarousel } from '@/components/HeroCarousel';
import { OutfitPostCard } from '@/components/OutfitPostCard';
import { OutfitTile } from '@/components/OutfitTile';
import { SectionHeader } from '@/components/SectionHeader';
import { banners } from '@/data/mock';
import { weatherLabel } from '@/data/profile';
import { useFeed } from '@/hooks/useFeed';
import { useTabBarOffset } from '@/hooks/useTabBarOffset';
import { useWeather } from '@/hooks/useWeather';
import { generateFeedOutfits, generateOccasionOutfits } from '@/lib/outfits';
import { useProfile } from '@/state/profile';
import { colors, layout, spacing } from '@/theme';

export default function HomeScreen() {
  const tabBarOffset = useTabBarOffset();
  const { profile } = useProfile();
  const { outfits, loading, hasMore, loadMore } = useFeed(profile.department, profile.styles);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <FlatList
        data={outfits}
        keyExtractor={(outfit) => outfit.id}
        renderItem={({ item }) => <OutfitPostCard outfit={item} />}
        ListHeaderComponent={<HomeHeader />}
        ListFooterComponent={<FeedFooter loading={loading} hasMore={hasMore} />}
        onEndReached={loadMore}
        onEndReachedThreshold={0.6}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingTop: spacing.sm, paddingBottom: tabBarOffset + layout.tabBarHeight + spacing.md }}
      />
    </SafeAreaView>
  );
}

function HomeHeader() {
  const { width } = useWindowDimensions();
  const { profile } = useProfile();
  const weather = useWeather();

  const looksOfTheDay = useMemo(
    () => generateFeedOutfits(profile.department, profile.styles).slice(0, 4),
    [profile.department, profile.styles],
  );
  const recommendations = useMemo(
    () => generateOccasionOutfits(profile.department, profile.styles),
    [profile.department, profile.styles],
  );

  const bannerWidth = Math.round(width * 0.66);
  // Три карточки целиком + небольшой «хвост» четвёртой, как на макете.
  const tileWidth = Math.round((width - spacing.md - spacing.sm * 2 - 28) / 3);

  return (
    <View>
      <FlatList
        data={banners}
        keyExtractor={(banner) => banner.id}
        renderItem={({ item }) => <BannerCard banner={item} width={bannerWidth} />}
        horizontal
        snapToInterval={bannerWidth + spacing.sm}
        decelerationRate="fast"
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.carousel}
        ItemSeparatorComponent={Gap}
      />

      <View style={styles.hero}>
        <HeroCarousel outfits={looksOfTheDay} label={weather ? `Образ дня · ${weatherLabel(weather)}` : 'Образ дня'} />
      </View>

      <View style={styles.section}>
        <SectionHeader title="Рекомендации для вас" actionLabel="Все" onActionPress={() => router.push('/recommendations')} />
        <FlatList
          data={recommendations}
          keyExtractor={(entry) => entry.outfit.id}
          renderItem={({ item }) => <OutfitTile tag={item.tag} outfit={item.outfit} width={tileWidth} />}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.carousel}
          ItemSeparatorComponent={Gap}
        />
      </View>

      <View style={[styles.section, styles.feedTitle]}>
        <SectionHeader title="Лента образов" />
      </View>
    </View>
  );
}

function Gap() {
  return <View style={styles.gap} />;
}

function FeedFooter({ loading, hasMore }: { loading: boolean; hasMore: boolean }) {
  if (loading) {
    return <ActivityIndicator style={styles.footer} color={colors.inkSoft} />;
  }
  if (!hasMore) {
    return <Text style={[styles.footer, styles.end]}>Вы посмотрели всё на сегодня</Text>;
  }
  return null;
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  carousel: {
    paddingHorizontal: spacing.md,
  },
  gap: {
    width: spacing.sm,
  },
  hero: {
    marginTop: spacing.md,
  },
  section: {
    marginTop: spacing.lg + spacing.xs,
  },
  feedTitle: {
    marginTop: spacing.xl,
  },
  footer: {
    paddingVertical: spacing.lg,
  },
  end: {
    textAlign: 'center',
    fontSize: 13,
    color: colors.inkSoft,
  },
});

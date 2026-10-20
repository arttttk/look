import { router } from 'expo-router';
import { useState } from 'react';
import {
  FlatList,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';

import { Icon } from '@/components/Icon';
import { LookCollage } from '@/components/LookCollage';
import type { Outfit } from '@/lib/outfits';
import { colors, radius, spacing } from '@/theme';

type Props = {
  outfits: Outfit[];
  // «Образ дня · 18°C, облачно»: погоду подставляет экран, у карусели её нет.
  label: string;
};

export function HeroCarousel({ outfits, label }: Props) {
  const { width } = useWindowDimensions();
  const [index, setIndex] = useState(0);

  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    setIndex(Math.round(event.nativeEvent.contentOffset.x / width));
  };

  return (
    <View>
      <FlatList
        data={outfits}
        keyExtractor={(outfit) => outfit.id}
        renderItem={({ item }) => <HeroSlide outfit={item} width={width} label={label} />}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onScroll={handleScroll}
        scrollEventThrottle={16}
      />
      <View style={styles.dots} pointerEvents="none">
        {outfits.map((outfit, i) => (
          <View key={outfit.id} style={[styles.dot, i === index && styles.dotActive]} />
        ))}
      </View>
    </View>
  );
}

function HeroSlide({ outfit, width, label }: { outfit: Outfit; width: number; label: string }) {
  return (
    <View style={{ width, paddingHorizontal: spacing.md }}>
      <View style={styles.card}>
        <LookCollage pieces={outfit.pieces} labels={false} style={styles.collage} />
        <View style={styles.text}>
          <Text style={styles.label}>{label}</Text>
          <Text style={styles.title}>{outfit.title}</Text>
        </View>
        <Pressable
          onPress={() => router.push({ pathname: '/look/[id]', params: { id: outfit.id } })}
          style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
          accessibilityRole="button"
          accessibilityLabel={`Смотреть образ: ${outfit.title}`}>
          <Text style={styles.ctaText}>Смотреть образ</Text>
          <Icon name="arrow-right" size={16} color={colors.ink} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    height: 184,
    borderRadius: radius.lg,
    overflow: 'hidden',
    backgroundColor: '#1E1D1C',
    padding: spacing.lg - 2,
    justifyContent: 'space-between',
  },
  collage: {
    position: 'absolute',
    top: spacing.md - 4,
    bottom: spacing.md - 4,
    right: spacing.xl + spacing.xs,
    width: '34%',
    borderRadius: radius.md,
  },
  text: {
    maxWidth: '52%',
    gap: spacing.sm,
  },
  label: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.onDarkSoft,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    lineHeight: 27,
    color: colors.onDark,
  },
  cta: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: spacing.sm,
    backgroundColor: colors.onDark,
    borderRadius: radius.pill,
    paddingVertical: 10,
    paddingHorizontal: spacing.md,
  },
  pressed: {
    opacity: 0.8,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.ink,
  },
  dots: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    right: spacing.md + spacing.sm,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(255,255,255,0.4)',
  },
  dotActive: {
    height: 18,
    backgroundColor: colors.onDark,
  },
});

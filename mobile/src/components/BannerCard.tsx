import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { Banner } from '@/data/mock';
import { colors, radius, spacing } from '@/theme';

type Props = {
  banner: Banner;
  width: number;
  onPress?: () => void;
};

export function BannerCard({ banner, width, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, { width, backgroundColor: banner.color }, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${banner.badge}. ${banner.title}`}>
      <Image source={banner.image} contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
      <LinearGradient
        colors={['rgba(0,0,0,0.82)', 'rgba(0,0,0,0.45)', 'rgba(0,0,0,0)']}
        locations={[0, 0.55, 1]}
        start={{ x: 0, y: 0.5 }}
        end={{ x: 1, y: 0.5 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{banner.badge}</Text>
      </View>
      <Text style={styles.title} numberOfLines={2}>
        {banner.title}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    height: 108,
    borderRadius: radius.lg,
    overflow: 'hidden',
    padding: spacing.md,
    justifyContent: 'space-between',
  },
  pressed: {
    opacity: 0.85,
  },
  badge: {
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.55)',
    borderRadius: radius.pill,
    paddingVertical: 3,
    paddingHorizontal: 10,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: colors.onDark,
  },
  title: {
    maxWidth: '78%',
    fontSize: 18,
    fontWeight: '800',
    lineHeight: 22,
    color: colors.onDark,
  },
});

import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { Look } from '@/data/mock';
import { colors, radius, spacing } from '@/theme';

type Props = {
  look: Look;
  onPress?: () => void;
};

export function HeroLook({ look, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, { backgroundColor: look.color }, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${look.tag}. ${look.title}`}>
      <View style={styles.pieces}>
        {look.pieces.map((piece, i) => (
          <Text key={i} style={styles.piece}>
            {piece}
          </Text>
        ))}
      </View>
      <View>
        <Text style={styles.tag}>{look.tag}</Text>
        <Text style={styles.title}>{look.title}</Text>
        <View style={styles.cta}>
          <Text style={styles.ctaText}>Смотреть образ</Text>
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: spacing.md,
    borderRadius: radius.lg,
    padding: spacing.lg,
    minHeight: 260,
    justifyContent: 'space-between',
  },
  pressed: {
    opacity: 0.9,
  },
  pieces: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  piece: {
    fontSize: 36,
  },
  tag: {
    fontSize: 13,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.7)',
    marginBottom: spacing.xs,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    lineHeight: 32,
    color: colors.onDark,
    marginBottom: spacing.md,
  },
  cta: {
    alignSelf: 'flex-start',
    backgroundColor: colors.onDark,
    borderRadius: radius.pill,
    paddingVertical: 10,
    paddingHorizontal: spacing.md,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.ink,
  },
});

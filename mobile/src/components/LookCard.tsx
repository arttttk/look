import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { Look } from '@/data/mock';
import { colors, radius, spacing } from '@/theme';

type Props = {
  look: Look;
  onPress?: () => void;
};

export function LookCard({ look, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${look.title}, ${look.tag}`}>
      <View style={[styles.preview, { backgroundColor: look.color }]}>
        <View style={styles.pieces}>
          {look.pieces.map((piece, i) => (
            <Text key={i} style={styles.piece}>
              {piece}
            </Text>
          ))}
        </View>
      </View>
      <Text style={styles.tag}>{look.tag}</Text>
      <Text style={styles.title} numberOfLines={2}>
        {look.title}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    width: 160,
  },
  pressed: {
    opacity: 0.7,
  },
  preview: {
    height: 200,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  pieces: {
    alignItems: 'center',
    gap: spacing.xs,
  },
  piece: {
    fontSize: 32,
  },
  tag: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.accent,
    marginBottom: 2,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.ink,
  },
});

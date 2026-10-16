import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { QuickAction } from '@/data/mock';
import { colors, radius, spacing } from '@/theme';

type Props = {
  action: QuickAction;
  onPress?: () => void;
};

export function QuickActionCard({ action, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${action.title}. ${action.subtitle}`}>
      <View style={styles.iconWrap}>
        <Text style={styles.icon}>{action.icon}</Text>
      </View>
      <Text style={styles.title} numberOfLines={1}>
        {action.title}
      </Text>
      <Text style={styles.subtitle} numberOfLines={1}>
        {action.subtitle}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: spacing.md,
    gap: 2,
  },
  pressed: {
    opacity: 0.7,
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: radius.pill,
    backgroundColor: colors.accentSoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  icon: {
    fontSize: 20,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.ink,
  },
  subtitle: {
    fontSize: 12,
    color: colors.inkSoft,
  },
});

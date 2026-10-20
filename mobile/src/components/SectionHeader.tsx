import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { colors, spacing } from '@/theme';

type Props = {
  title: string;
  actionLabel?: string;
  onActionPress?: () => void;
};

export function SectionHeader({ title, actionLabel, onActionPress }: Props) {
  return (
    <View style={styles.row}>
      <Text style={styles.title} accessibilityRole="header">
        {title}
      </Text>
      {actionLabel ? (
        <Pressable onPress={onActionPress} hitSlop={8} style={styles.action} accessibilityRole="button">
          <Text style={styles.actionText}>{actionLabel}</Text>
          <Icon name="arrow-right" size={16} color={colors.inkSoft} />
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    marginBottom: spacing.md,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.ink,
  },
  action: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  actionText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.inkSoft,
  },
});

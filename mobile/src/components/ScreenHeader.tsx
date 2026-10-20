import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { closeScreen } from '@/lib/navigation';
import { colors, radius, spacing } from '@/theme';

type Props = {
  title?: string;
  right?: ReactNode;
  // x — для модальных экранов, arrow — для обычных.
  icon?: 'arrow-left' | 'x';
};

export function ScreenHeader({ title, right, icon = 'arrow-left' }: Props) {
  return (
    <View style={styles.row}>
      <Pressable
        onPress={closeScreen}
        hitSlop={8}
        style={styles.back}
        accessibilityRole="button"
        accessibilityLabel={icon === 'x' ? 'Закрыть' : 'Назад'}>
        <Icon name={icon} size={20} color={colors.ink} />
      </Pressable>
      {title ? (
        <Text style={styles.title} numberOfLines={1} accessibilityRole="header">
          {title}
        </Text>
      ) : null}
      <View style={styles.spacer} />
      {right}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md - 4,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  back: {
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    flexShrink: 1,
    fontSize: 20,
    fontWeight: '800',
    color: colors.ink,
  },
  spacer: {
    flex: 1,
  },
});

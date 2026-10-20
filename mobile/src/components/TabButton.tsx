import type { TabTriggerSlotProps } from 'expo-router/ui';
import type { Ref } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, type IconName } from '@/components/Icon';
import { colors, radius, spacing } from '@/theme';

type Props = TabTriggerSlotProps & {
  icon: IconName;
  label: string;
  // Кнопка с постоянной «плашкой» под главное действие (Примерить).
  highlighted?: boolean;
  ref?: Ref<View>;
};

export function TabButton({ icon, label, highlighted, isFocused, ...props }: Props) {
  const tint = isFocused ? colors.ink : colors.inkSoft;

  return (
    <Pressable
      {...props}
      style={styles.slot}
      accessibilityRole="tab"
      accessibilityState={{ selected: !!isFocused }}
      accessibilityLabel={label}>
      <View style={[styles.inner, highlighted && styles.highlighted]}>
        <Icon name={icon} size={24} color={tint} filled={isFocused} cutout={colors.surface} />
        <Text style={[styles.label, isFocused && styles.labelActive]} numberOfLines={1}>
          {label}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  slot: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  inner: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
    minWidth: 72,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.md,
  },
  highlighted: {
    backgroundColor: colors.chip,
  },
  label: {
    fontSize: 11,
    fontWeight: '500',
    color: colors.inkSoft,
  },
  labelActive: {
    fontWeight: '800',
    color: colors.ink,
  },
});

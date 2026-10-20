import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { colors, radius, spacing } from '@/theme';

type PrimaryProps = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
};

export function PrimaryButton({ label, onPress, disabled, loading }: PrimaryProps) {
  const inactive = disabled || loading;

  return (
    <Pressable
      onPress={onPress}
      disabled={inactive}
      style={({ pressed }) => [styles.primary, disabled && styles.primaryDisabled, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityState={{ disabled: !!inactive, busy: !!loading }}>
      {loading ? (
        <ActivityIndicator color={colors.onDark} />
      ) : (
        <Text style={[styles.primaryText, disabled && styles.primaryTextDisabled]}>{label}</Text>
      )}
    </Pressable>
  );
}

type TextProps = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
};

export function TextButton({ label, onPress, disabled }: TextProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      hitSlop={8}
      style={styles.text}
      accessibilityRole="button"
      accessibilityState={{ disabled: !!disabled }}>
      <Text style={[styles.textLabel, disabled && styles.textLabelDisabled]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  primary: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 52,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
  },
  primaryDisabled: {
    backgroundColor: colors.chip,
  },
  pressed: {
    opacity: 0.85,
  },
  primaryText: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onDark,
  },
  primaryTextDisabled: {
    color: colors.inkSoft,
  },
  text: {
    alignItems: 'center',
    paddingVertical: spacing.sm + 2,
  },
  textLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.inkSoft,
  },
  textLabelDisabled: {
    opacity: 0.5,
  },
});

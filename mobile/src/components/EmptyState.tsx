import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon, type IconName } from '@/components/Icon';
import { colors, radius, spacing } from '@/theme';

type Props = {
  icon: IconName;
  title: string;
  text: string;
  actionLabel?: string;
  onAction?: () => void;
  children?: ReactNode;
};

export function EmptyState({ icon, title, text, actionLabel, onAction, children }: Props) {
  return (
    <View style={styles.wrap}>
      <View style={styles.circle}>
        <Icon name={icon} size={30} color={colors.inkSoft} />
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.text}>{text}</Text>
      {actionLabel ? (
        <Pressable
          onPress={onAction}
          style={({ pressed }) => [styles.button, pressed && styles.pressed]}
          accessibilityRole="button">
          <Text style={styles.buttonText}>{actionLabel}</Text>
        </Pressable>
      ) : null}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: 'center',
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.xl,
    gap: spacing.sm,
  },
  circle: {
    width: 72,
    height: 72,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.ink,
    textAlign: 'center',
  },
  text: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.inkSoft,
    textAlign: 'center',
  },
  button: {
    marginTop: spacing.md,
    height: 48,
    paddingHorizontal: spacing.lg,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pressed: {
    opacity: 0.85,
  },
  buttonText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onDark,
  },
});

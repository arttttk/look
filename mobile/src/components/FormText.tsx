import { StyleSheet, Text } from 'react-native';

import { colors, spacing } from '@/theme';

export function Brand() {
  return <Text style={styles.brand}>Look</Text>;
}

export function Title({ children }: { children: string }) {
  return (
    <Text style={styles.title} accessibilityRole="header">
      {children}
    </Text>
  );
}

export function Subtitle({ children }: { children: string }) {
  return <Text style={styles.subtitle}>{children}</Text>;
}

export function ErrorText({ children }: { children: string | null }) {
  return children ? (
    <Text style={styles.error} accessibilityRole="alert">
      {children}
    </Text>
  ) : null;
}

const styles = StyleSheet.create({
  brand: {
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 3,
    textTransform: 'uppercase',
    color: colors.inkSoft,
    marginBottom: spacing.sm,
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
    lineHeight: 34,
    color: colors.ink,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 21,
    color: colors.inkSoft,
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  error: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.like,
    marginTop: spacing.md,
  },
});

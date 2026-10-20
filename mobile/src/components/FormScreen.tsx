import type { ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors, spacing } from '@/theme';

type Props = {
  top?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
};

// Каркас экранов-форм: верхняя панель, прокручиваемое содержимое и закреплённый низ с кнопками.
export function FormScreen({ top, footer, children }: Props) {
  const { bottom } = useSafeAreaInsets();

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {top}
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}>
          {children}
        </ScrollView>
        {footer ? <View style={[styles.footer, { paddingBottom: Math.max(bottom, spacing.md) }]}>{footer}</View> : null}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  flex: {
    flex: 1,
  },
  content: {
    padding: spacing.md,
    paddingTop: spacing.lg,
  },
  footer: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    gap: spacing.xs,
    backgroundColor: colors.bg,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
});

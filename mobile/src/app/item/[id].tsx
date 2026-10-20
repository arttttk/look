import { Image } from 'expo-image';
import { useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { EmptyState } from '@/components/EmptyState';
import { Icon } from '@/components/Icon';
import { ScreenHeader } from '@/components/ScreenHeader';
import { categoryTitle, colorById } from '@/data/taxonomy';
import { itemLabel } from '@/data/wardrobe';
import { closeScreen } from '@/lib/navigation';
import { useWardrobe } from '@/state/wardrobe';
import { colors, radius, spacing } from '@/theme';

export default function ItemScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { ready, items, removeItem } = useWardrobe();
  const [confirming, setConfirming] = useState(false);

  const item = items.find((entry) => entry.id === id);

  if (!ready) return <SafeAreaView style={styles.safe} />;

  if (!item) {
    return (
      <SafeAreaView style={styles.safe}>
        <ScreenHeader />
        <EmptyState
          icon="shirt"
          title="Вещь не найдена"
          text="Возможно, она уже удалена из гардероба."
          actionLabel="Вернуться"
          onAction={closeScreen}
        />
      </SafeAreaView>
    );
  }

  const color = colorById(item.color);

  const remove = () => {
    removeItem(item.id);
    closeScreen();
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <ScreenHeader title={itemLabel(item)} />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={[styles.photo, { backgroundColor: color.hex }]}>
          <Image source={item.image} contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
        </View>

        <View style={styles.meta}>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{categoryTitle(item.category)}</Text>
          </View>
          <View style={styles.badge}>
            <View style={[styles.swatch, { backgroundColor: color.hex }]} />
            <Text style={styles.badgeText}>{color.title}</Text>
          </View>
        </View>

        {confirming ? (
          <View style={styles.confirm}>
            <Text style={styles.confirmText}>Удалить вещь из гардероба? Это действие нельзя отменить.</Text>
            <View style={styles.confirmRow}>
              <Pressable onPress={() => setConfirming(false)} style={[styles.button, styles.buttonGhost]} accessibilityRole="button">
                <Text style={styles.buttonGhostText}>Отмена</Text>
              </Pressable>
              <Pressable onPress={remove} style={[styles.button, styles.buttonDanger]} accessibilityRole="button">
                <Text style={styles.buttonDangerText}>Удалить</Text>
              </Pressable>
            </View>
          </View>
        ) : (
          <Pressable
            onPress={() => setConfirming(true)}
            style={({ pressed }) => [styles.remove, pressed && styles.pressed]}
            accessibilityRole="button">
            <Icon name="trash" size={18} color={colors.like} />
            <Text style={styles.removeText}>Удалить из гардероба</Text>
          </Pressable>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    padding: spacing.md,
    gap: spacing.md,
  },
  photo: {
    aspectRatio: 0.85,
    borderRadius: radius.lg,
    overflow: 'hidden',
  },
  meta: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md - 2,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
  },
  badgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.ink,
  },
  swatch: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.15)',
  },
  remove: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    height: 50,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.like,
  },
  pressed: {
    opacity: 0.7,
  },
  removeText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.like,
  },
  confirm: {
    gap: spacing.md,
  },
  confirmText: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.inkSoft,
    textAlign: 'center',
  },
  confirmRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  button: {
    flex: 1,
    height: 50,
    borderRadius: radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonGhost: {
    backgroundColor: colors.chip,
  },
  buttonGhostText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.ink,
  },
  buttonDanger: {
    backgroundColor: colors.like,
  },
  buttonDangerText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onDark,
  },
});

import { TabList, TabSlot, TabTrigger, Tabs } from 'expo-router/ui';
import { StyleSheet } from 'react-native';

import { TabButton } from '@/components/TabButton';
import { useTabBarOffset } from '@/hooks/useTabBarOffset';
import { colors, layout, radius, spacing } from '@/theme';

export default function TabsLayout() {
  const offset = useTabBarOffset();

  return (
    <Tabs>
      <TabSlot />
      <TabList style={[styles.bar, { bottom: offset }]}>
        <TabTrigger name="index" href="/" asChild>
          <TabButton icon="home" label="Для тебя" />
        </TabTrigger>
        <TabTrigger name="wardrobe" href="/wardrobe" asChild>
          <TabButton icon="shirt" label="Гардероб" />
        </TabTrigger>
        <TabTrigger name="try-on" href="/try-on" asChild>
          <TabButton icon="scan" label="Примерить" highlighted />
        </TabTrigger>
        <TabTrigger name="looks" href="/looks" asChild>
          <TabButton icon="heart" label="Образы" />
        </TabTrigger>
        <TabTrigger name="profile" href="/profile" asChild>
          <TabButton icon="user" label="Профиль" />
        </TabTrigger>
      </TabList>
    </Tabs>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: 'absolute',
    left: spacing.sm + spacing.xs,
    right: spacing.sm + spacing.xs,
    height: layout.tabBarHeight,
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.lg + spacing.xs,
    borderWidth: 1,
    borderColor: colors.line,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
});

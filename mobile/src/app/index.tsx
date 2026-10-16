import { FlatList, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { HeroLook } from '@/components/HeroLook';
import { LookCard } from '@/components/LookCard';
import { QuickActionCard } from '@/components/QuickActionCard';
import { SectionHeader } from '@/components/SectionHeader';
import { lookOfTheDay, quickActions, recommendations } from '@/data/mock';
import { colors, spacing } from '@/theme';

export default function HomeScreen() {
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.brand}>Look</Text>
          <Text style={styles.greeting}>Что наденем сегодня?</Text>
        </View>

        <HeroLook look={lookOfTheDay} />

        <View style={styles.section}>
          <View style={styles.actions}>
            {quickActions.map((action) => (
              <QuickActionCard key={action.id} action={action} />
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <SectionHeader title="Рекомендации для вас" actionLabel="Все" />
          <FlatList
            data={recommendations}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => <LookCard look={item} />}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.carousel}
            ItemSeparatorComponent={() => <View style={styles.gap} />}
          />
        </View>
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
    paddingBottom: spacing.xl,
  },
  header: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    paddingBottom: spacing.lg,
  },
  brand: {
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 3,
    textTransform: 'uppercase',
    color: colors.accent,
    marginBottom: spacing.xs,
  },
  greeting: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.ink,
  },
  section: {
    marginTop: spacing.xl,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  carousel: {
    paddingHorizontal: spacing.md,
  },
  gap: {
    width: spacing.md,
  },
});

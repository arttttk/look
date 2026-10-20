import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Icon } from '@/components/Icon';
import { useTabBarOffset } from '@/hooks/useTabBarOffset';
import { colors, layout, radius, spacing } from '@/theme';

const STEPS = [
  { title: 'Загрузите своё фото', text: 'Фото в полный рост на нейтральном фоне.' },
  { title: 'Выберите образ или вещь', text: 'Из гардероба, избранного или каталога.' },
  { title: 'Посмотрите, как сидит', text: 'Мы наденем вещи на ваше фото.' },
];

// Реальная примерка требует ИИ-сервиса на бэкенде — пока экран честно говорит, что она в разработке.
export default function TryOnScreen() {
  const tabBarOffset = useTabBarOffset();

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: tabBarOffset + layout.tabBarHeight + spacing.md }]}
        showsVerticalScrollIndicator={false}>
        <Text style={styles.title}>Примерить</Text>

        <View style={styles.hero}>
          <View style={styles.heroIcon}>
            <Icon name="scan" size={34} color={colors.onDark} />
          </View>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>Скоро</Text>
          </View>
          <Text style={styles.heroTitle}>Виртуальная примерка</Text>
          <Text style={styles.heroText}>Посмотрите, как вещь выглядит на вас, ещё до покупки.</Text>
        </View>

        <Text style={styles.heading}>Как это будет работать</Text>
        <View style={styles.steps}>
          {STEPS.map((step, index) => (
            <View key={step.title} style={styles.step}>
              <View style={styles.number}>
                <Text style={styles.numberText}>{index + 1}</Text>
              </View>
              <View style={styles.stepText}>
                <Text style={styles.stepTitle}>{step.title}</Text>
                <Text style={styles.stepSub}>{step.text}</Text>
              </View>
            </View>
          ))}
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
    padding: spacing.md,
    paddingTop: spacing.md,
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.ink,
    marginBottom: spacing.md,
  },
  hero: {
    alignItems: 'center',
    padding: spacing.lg,
    borderRadius: radius.lg,
    backgroundColor: '#1E1D1C',
    gap: spacing.sm,
  },
  heroIcon: {
    width: 72,
    height: 72,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(255,255,255,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badge: {
    paddingVertical: 3,
    paddingHorizontal: 10,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.55)',
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: colors.onDark,
  },
  heroTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.onDark,
  },
  heroText: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.onDarkSoft,
    textAlign: 'center',
  },
  heading: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.ink,
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  steps: {
    gap: spacing.md,
  },
  step: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  number: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
    alignItems: 'center',
    justifyContent: 'center',
  },
  numberText: {
    fontSize: 15,
    fontWeight: '800',
    color: colors.ink,
  },
  stepText: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: colors.ink,
  },
  stepSub: {
    fontSize: 13,
    color: colors.inkSoft,
    marginTop: 2,
  },
});

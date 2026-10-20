import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { PrimaryButton } from '@/components/Buttons';
import { Brand, Subtitle, Title } from '@/components/FormText';
import { FormScreen } from '@/components/FormScreen';
import { Icon, type IconName } from '@/components/Icon';
import { colors, radius, spacing } from '@/theme';

const FEATURES: { icon: IconName; title: string; text: string }[] = [
  { icon: 'camera', title: 'Сфотографируй гардероб', text: 'Добавь свои вещи — это займёт пару минут' },
  { icon: 'heart', title: 'Получай готовые образы', text: 'Сочетаем цвета, стили и погоду автоматически' },
  { icon: 'shirt', title: 'Докупай недостающее', text: 'Подсказываем вещи из магазинов-партнёров' },
];

export default function WelcomeScreen() {
  return (
    <FormScreen footer={<PrimaryButton label="Продолжить" onPress={() => router.push('/login')} />}>
      <Brand />
      <Title>Твой личный стилист</Title>
      <Subtitle>Собираем образы из твоих вещей и подсказываем, что докупить.</Subtitle>

      <View style={styles.features}>
        {FEATURES.map((feature) => (
          <View key={feature.title} style={styles.feature}>
            <View style={styles.icon}>
              <Icon name={feature.icon} size={22} color={colors.ink} />
            </View>
            <View style={styles.text}>
              <Text style={styles.featureTitle}>{feature.title}</Text>
              <Text style={styles.featureText}>{feature.text}</Text>
            </View>
          </View>
        ))}
      </View>
    </FormScreen>
  );
}

const styles = StyleSheet.create({
  features: {
    gap: spacing.md,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  icon: {
    width: 48,
    height: 48,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.ink,
  },
  featureText: {
    fontSize: 13,
    color: colors.inkSoft,
    marginTop: 2,
  },
});

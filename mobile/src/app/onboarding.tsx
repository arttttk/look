import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { PrimaryButton, TextButton } from '@/components/Buttons';
import { ErrorText, Subtitle, Title } from '@/components/FormText';
import { FormScreen } from '@/components/FormScreen';
import { Icon } from '@/components/Icon';
import { AboutStep } from '@/components/profile/AboutStep';
import { BudgetStep } from '@/components/profile/BudgetStep';
import { DepartmentStep } from '@/components/profile/DepartmentStep';
import { LocationStep } from '@/components/profile/LocationStep';
import { StylesStep } from '@/components/profile/StylesStep';
import type { Budget, Location } from '@/data/profile';
import type { StyleId } from '@/data/styles';
import type { Department } from '@/data/taxonomy';
import { ApiError } from '@/lib/api';
import { cleanName, parseBirthYear, validateName } from '@/lib/profileForm';
import { useProfile } from '@/state/profile';
import { colors, radius, spacing } from '@/theme';

type Step = 'about' | 'department' | 'location' | 'budget' | 'styles';

const STEPS: Step[] = ['about', 'department', 'location', 'budget', 'styles'];

const COPY: Record<Step, { title: string; subtitle: string }> = {
  about: { title: 'Давай знакомиться', subtitle: 'Так мы сможем обращаться к тебе по имени.' },
  department: { title: 'Для кого подбираем?', subtitle: 'Покажем одежду и образы, которые подойдут именно тебе.' },
  location: { title: 'Где ты живёшь?', subtitle: 'Узнаем погоду и подберём образы под неё.' },
  budget: { title: 'Какой бюджет на образ?', subtitle: 'Не будем предлагать то, что не по карману.' },
  styles: { title: 'Какой у тебя стиль?', subtitle: 'Выбери один или несколько — лента и образы подстроятся. Это можно изменить в профиле.' },
};

export default function OnboardingScreen() {
  const { completeOnboarding } = useProfile();
  const [index, setIndex] = useState(0);
  const [name, setName] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [department, setDepartment] = useState<Department | null>(null);
  const [location, setLocation] = useState<Location | null>(null);
  const [budget, setBudget] = useState<Budget | null>(null);
  const [selectedStyles, setSelectedStyles] = useState<StyleId[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = STEPS[index];
  const isLast = index === STEPS.length - 1;

  const year = parseBirthYear(birthYear);
  const yearError = year === undefined ? 'Введите год из четырёх цифр, например 1998' : null;
  const nameError = validateName(name);
  const canGoNext =
    (step === 'about' && !yearError && !nameError) || (step === 'department' && department !== null) || step === 'location' || step === 'budget';

  const finish = async (chosenStyles: StyleId[]) => {
    setSaving(true);
    setError(null);
    try {
      await completeOnboarding({
        department: department ?? 'any',
        styles: chosenStyles,
        name: cleanName(name) || null,
        birth_year: year ?? null,
        location,
        budget,
      });
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : 'Не удалось сохранить профиль.');
      setSaving(false);
    }
  };

  const next = () => setIndex((current) => Math.min(current + 1, STEPS.length - 1));

  return (
    <FormScreen
      top={
        <View style={styles.top}>
          {index > 0 ? (
            <Pressable
              onPress={() => setIndex((current) => current - 1)}
              hitSlop={8}
              style={styles.back}
              accessibilityRole="button"
              accessibilityLabel="Назад">
              <Icon name="arrow-left" size={20} color={colors.ink} />
            </Pressable>
          ) : (
            <View style={styles.back} />
          )}
          <View style={styles.progress} accessibilityLabel={`Шаг ${index + 1} из ${STEPS.length}`}>
            {STEPS.map((id, i) => (
              <View key={id} style={[styles.bar, i <= index && styles.barActive]} />
            ))}
          </View>
          <View style={styles.back} />
        </View>
      }
      footer={
        isLast ? (
          <>
            <PrimaryButton
              label={selectedStyles.length > 0 ? `Готово · ${selectedStyles.length}` : 'Выбери хотя бы один стиль'}
              disabled={selectedStyles.length === 0}
              loading={saving}
              onPress={() => void finish(selectedStyles)}
            />
            <TextButton label="Пока не определился" disabled={saving} onPress={() => void finish([])} />
          </>
        ) : (
          <>
            <PrimaryButton label="Далее" disabled={!canGoNext} onPress={next} />
            {step === 'about' || step === 'location' || step === 'budget' ? (
              <TextButton label="Пропустить" onPress={next} />
            ) : null}
          </>
        )
      }>
      <Title>{COPY[step].title}</Title>
      <Subtitle>{COPY[step].subtitle}</Subtitle>

      {step === 'about' && (
        <AboutStep
          name={name}
          birthYear={birthYear}
          onChangeName={setName}
          onChangeBirthYear={setBirthYear}
          birthYearError={birthYear.length === 4 ? yearError : null}
        />
      )}
      {step === 'department' && <DepartmentStep value={department} onChange={setDepartment} />}
      {step === 'location' && <LocationStep value={location} onChange={setLocation} />}
      {step === 'budget' && <BudgetStep value={budget} onChange={setBudget} />}
      {step === 'styles' && <StylesStep selected={selectedStyles} onChange={setSelectedStyles} />}

      <ErrorText>{error}</ErrorText>
    </FormScreen>
  );
}

const styles = StyleSheet.create({
  top: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
  },
  back: {
    width: 38,
    height: 38,
    borderRadius: radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  progress: {
    flexDirection: 'row',
    gap: 6,
  },
  bar: {
    width: 28,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.chip,
  },
  barActive: {
    backgroundColor: colors.ink,
  },
});

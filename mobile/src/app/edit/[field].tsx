import { useLocalSearchParams } from 'expo-router';
import { useState } from 'react';

import { PrimaryButton } from '@/components/Buttons';
import { ErrorText, Subtitle, Title } from '@/components/FormText';
import { FormScreen } from '@/components/FormScreen';
import { AboutStep } from '@/components/profile/AboutStep';
import { BudgetStep } from '@/components/profile/BudgetStep';
import { DepartmentStep } from '@/components/profile/DepartmentStep';
import { LocationStep } from '@/components/profile/LocationStep';
import { StylesStep } from '@/components/profile/StylesStep';
import { ScreenHeader } from '@/components/ScreenHeader';
import type { Budget, Location, ProfilePatch } from '@/data/profile';
import type { StyleId } from '@/data/styles';
import type { Department } from '@/data/taxonomy';
import { ApiError } from '@/lib/api';
import { closeScreen } from '@/lib/navigation';
import { cleanName, parseBirthYear, validateName } from '@/lib/profileForm';
import { useProfile } from '@/state/profile';

const TITLES: Record<string, { title: string; subtitle: string }> = {
  about: { title: 'О тебе', subtitle: 'Имя и год рождения.' },
  department: { title: 'Для кого подбираем', subtitle: 'От этого зависит одежда в ленте и в образах.' },
  location: { title: 'Город', subtitle: 'По нему мы узнаём погоду.' },
  budget: { title: 'Бюджет', subtitle: 'Потолок цены одного образа.' },
  styles: { title: 'Мои стили', subtitle: 'Можно выбрать несколько или не выбирать ни одного.' },
};

export default function EditProfileScreen() {
  const { field } = useLocalSearchParams<{ field: string }>();
  const { profile, update } = useProfile();

  const [name, setName] = useState(profile.name ?? '');
  const [birthYear, setBirthYear] = useState(profile.birth_year?.toString() ?? '');
  const [department, setDepartment] = useState<Department | null>(profile.department);
  const [location, setLocation] = useState<Location | null>(profile.location);
  const [budget, setBudget] = useState<Budget | null>(profile.budget);
  const [styles, setStyles] = useState<StyleId[]>(profile.styles);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const copy = TITLES[field] ?? { title: 'Профиль', subtitle: '' };
  const year = parseBirthYear(birthYear);
  const yearError = year === undefined ? 'Введите год из четырёх цифр, например 1998' : null;
  const nameError = validateName(name);

  const patch = (): ProfilePatch | null => {
    switch (field) {
      case 'about':
        return yearError || nameError ? null : { name: cleanName(name) || null, birth_year: year ?? null };
      case 'department':
        return department ? { department } : null;
      case 'location':
        return { location };
      case 'budget':
        return { budget };
      case 'styles':
        return { styles };
      default:
        return null;
    }
  };

  const changes = patch();

  const save = async () => {
    if (!changes) return;
    setSaving(true);
    setError(null);
    try {
      await update(changes);
      closeScreen();
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : 'Не удалось сохранить.');
      setSaving(false);
    }
  };

  return (
    <FormScreen
      top={<ScreenHeader icon="x" />}
      footer={<PrimaryButton label="Сохранить" disabled={!changes} loading={saving} onPress={() => void save()} />}>
      <Title>{copy.title}</Title>
      {copy.subtitle ? <Subtitle>{copy.subtitle}</Subtitle> : null}

      {field === 'about' && (
        <AboutStep
          name={name}
          birthYear={birthYear}
          onChangeName={setName}
          onChangeBirthYear={setBirthYear}
          birthYearError={birthYear.length === 4 ? yearError : null}
        />
      )}
      {field === 'department' && <DepartmentStep value={department} onChange={setDepartment} />}
      {field === 'location' && <LocationStep value={location} onChange={setLocation} />}
      {field === 'budget' && <BudgetStep value={budget} onChange={setBudget} />}
      {field === 'styles' && <StylesStep selected={styles} onChange={setStyles} />}

      <ErrorText>{error}</ErrorText>
    </FormScreen>
  );
}

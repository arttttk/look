import { router } from 'expo-router';
import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Icon } from '@/components/Icon';
import { budgetTitle, weatherLabel } from '@/data/profile';
import { styleTitle } from '@/data/styles';
import { departments } from '@/data/taxonomy';
import { useTabBarOffset } from '@/hooks/useTabBarOffset';
import { useWeather } from '@/hooks/useWeather';
import { describeContact } from '@/lib/profileForm';
import { useAuth } from '@/state/auth';
import { useFavorites } from '@/state/favorites';
import { useProfile } from '@/state/profile';
import { useWardrobe } from '@/state/wardrobe';
import { colors, layout, radius, spacing } from '@/theme';

type Field = 'about' | 'department' | 'location' | 'budget' | 'styles';

export default function ProfileScreen() {
  const tabBarOffset = useTabBarOffset();
  const { profile } = useProfile();
  const { signOut } = useAuth();
  const { items } = useWardrobe();
  const { ids } = useFavorites();
  const weather = useWeather();

  const department = departments.find((option) => option.id === profile.department);
  const initial = (profile.name ?? describeContact(profile.phone, profile.email)).trim().charAt(0).toUpperCase() || 'L';
  const undecided = profile.styles.length === 0;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: tabBarOffset + layout.tabBarHeight + spacing.md }]}
        showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initial}</Text>
          </View>
          <View style={styles.headerText}>
            <Text style={styles.name} numberOfLines={1}>
              {profile.name ?? 'Профиль'}
            </Text>
            <Text style={styles.contact} numberOfLines={1}>
              {describeContact(profile.phone, profile.email)}
            </Text>
          </View>
        </View>

        {profile.location ? (
          <View style={styles.weather}>
            <Text style={styles.weatherCity}>{profile.location.city}</Text>
            <Text style={styles.weatherText}>{weather ? weatherLabel(weather) : 'Погода пока недоступна'}</Text>
          </View>
        ) : null}

        <View style={styles.stats}>
          <Stat value={items.length} label="вещей в гардеробе" />
          <Stat value={ids.length} label="образов в избранном" />
        </View>

        <View style={styles.list}>
          <Row label="О тебе" value={aboutValue(profile.name, profile.birth_year)} field="about" />
          <Row label="Подбираем для" value={department?.title ?? 'Без разницы'} field="department" />
          <Row label="Город" value={profile.location ? profile.location.city : 'Не указан'} field="location" />
          <Row label="Бюджет на образ" value={budgetTitle(profile.budget)} field="budget" />
          <Row
            label="Мои стили"
            value={undecided ? 'Не определился' : profile.styles.map(styleTitle).join(', ')}
            field="styles"
          />
        </View>

        {undecided && profile.regional_styles.length > 0 ? (
          <Text style={styles.note}>
            Пока стили не выбраны, подбираем по региону: {profile.regional_styles.map(styleTitle).join(', ')}.
          </Text>
        ) : null}

        <Pressable
          onPress={() => void signOut()}
          style={({ pressed }) => [styles.signOut, pressed && styles.pressed]}
          accessibilityRole="button">
          <Text style={styles.signOutText}>Выйти</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function aboutValue(name: string | null, birthYear: number | null) {
  const parts = [name, birthYear ? `${birthYear} г.р.` : null].filter(Boolean);
  return parts.length > 0 ? parts.join(', ') : 'Не указано';
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function Row({ label, value, field }: { label: string; value: ReactNode; field: Field }) {
  return (
    <Pressable
      onPress={() => router.push({ pathname: '/edit/[field]', params: { field } })}
      style={({ pressed }) => [styles.row, pressed && styles.pressed]}
      accessibilityRole="button"
      accessibilityLabel={`${label}: изменить`}>
      <View style={styles.rowText}>
        <Text style={styles.rowLabel}>{label}</Text>
        <Text style={styles.rowValue} numberOfLines={2}>
          {value}
        </Text>
      </View>
      <Icon name="arrow-right" size={18} color={colors.inkSoft} />
    </Pressable>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: '800',
    color: colors.onDark,
  },
  headerText: {
    flex: 1,
  },
  name: {
    fontSize: 24,
    fontWeight: '800',
    color: colors.ink,
  },
  contact: {
    fontSize: 14,
    color: colors.inkSoft,
    marginTop: 2,
  },
  weather: {
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.ink,
    marginBottom: spacing.md,
  },
  weatherCity: {
    fontSize: 13,
    color: colors.onDarkSoft,
  },
  weatherText: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.onDark,
    marginTop: 2,
  },
  stats: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  stat: {
    flex: 1,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
  },
  statValue: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.ink,
  },
  statLabel: {
    fontSize: 12,
    color: colors.inkSoft,
    marginTop: 2,
  },
  list: {
    gap: spacing.sm,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
  },
  pressed: {
    opacity: 0.7,
  },
  rowText: {
    flex: 1,
  },
  rowLabel: {
    fontSize: 12,
    color: colors.inkSoft,
  },
  rowValue: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.ink,
    marginTop: 2,
  },
  note: {
    fontSize: 13,
    lineHeight: 18,
    color: colors.inkSoft,
    marginTop: spacing.md,
  },
  signOut: {
    alignSelf: 'center',
    marginTop: spacing.lg,
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.lg,
  },
  signOutText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.like,
  },
});

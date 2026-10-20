import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';

import { PrimaryButton } from '@/components/Buttons';
import { AuthProvider, useAuth } from '@/state/auth';
import { FavoritesProvider } from '@/state/favorites';
import { ProfileProvider, useProfile } from '@/state/profile';
import { WardrobeProvider } from '@/state/wardrobe';
import { colors, spacing } from '@/theme';

export default function RootLayout() {
  return (
    <AuthProvider>
      <ProfileProvider>
        <StatusBar style="dark" />
        <RootNavigator />
      </ProfileProvider>
    </AuthProvider>
  );
}

const screenOptions = { headerShown: false, contentStyle: { backgroundColor: colors.bg } };

function RootNavigator() {
  const { status } = useAuth();
  const profile = useProfile();

  // Пока читаем токен и профиль — пустой экран: показывать вход или главную рано.
  if (status === 'loading' || (status === 'signedIn' && (profile.status === 'idle' || profile.status === 'loading'))) {
    return null;
  }

  if (status === 'signedIn' && profile.status === 'error') {
    return (
      <View style={styles.retry}>
        <Text style={styles.retryTitle}>Не удалось загрузить профиль</Text>
        <Text style={styles.retryText}>{profile.error}</Text>
        <PrimaryButton label="Повторить" onPress={profile.reload} />
      </View>
    );
  }

  const signedIn = status === 'signedIn';
  const onboarded = signedIn && profile.profile.onboarded;

  return (
    // Данные на устройстве (гардероб, избранное) привязаны к пользователю: key пересоздаёт их при смене аккаунта.
    <WardrobeProvider key={profile.profile.id || 'guest'}>
      <FavoritesProvider key={profile.profile.id || 'guest'}>
        <Stack screenOptions={screenOptions}>
          <Stack.Protected guard={!signedIn}>
            <Stack.Screen name="welcome" />
            <Stack.Screen name="login" />
            <Stack.Screen name="code" />
          </Stack.Protected>
          <Stack.Protected guard={signedIn && !onboarded}>
            <Stack.Screen name="onboarding" />
          </Stack.Protected>
          <Stack.Protected guard={onboarded}>
            <Stack.Screen name="(tabs)" />
            <Stack.Screen name="add-item" options={{ presentation: 'modal' }} />
            <Stack.Screen name="edit/[field]" options={{ presentation: 'modal' }} />
            <Stack.Screen name="item/[id]" />
            <Stack.Screen name="look/[id]" />
            <Stack.Screen name="recommendations" />
          </Stack.Protected>
        </Stack>
      </FavoritesProvider>
    </WardrobeProvider>
  );
}

const styles = StyleSheet.create({
  retry: {
    flex: 1,
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.lg,
    backgroundColor: colors.bg,
  },
  retryTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.ink,
  },
  retryText: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.inkSoft,
  },
});

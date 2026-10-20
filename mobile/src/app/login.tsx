import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { PrimaryButton } from '@/components/Buttons';
import { ErrorText, Subtitle, Title } from '@/components/FormText';
import { FormScreen } from '@/components/FormScreen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { ApiError } from '@/lib/api';
import { looksLikeEmail } from '@/lib/profileForm';
import { useAuth } from '@/state/auth';
import { colors, radius, spacing } from '@/theme';

type Kind = 'phone' | 'email';

const KINDS: { id: Kind; label: string }[] = [
  { id: 'phone', label: 'Телефон' },
  { id: 'email', label: 'Почта' },
];

export default function LoginScreen() {
  const { requestCode } = useAuth();
  const [kind, setKind] = useState<Kind>('phone');
  const [value, setValue] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const identifier = value.trim();
  const canSend = identifier.length >= 3 && !sending;

  const send = async () => {
    setSending(true);
    setError(null);
    try {
      const issued = await requestCode(identifier);
      router.push({
        pathname: '/code',
        params: {
          identifier: issued.identifier,
          resendAfter: String(issued.resend_after),
          devCode: issued.dev_code ?? '',
        },
      });
    } catch (failure) {
      // Код уже отправляли недавно: пускаем на экран ввода, он покажет, через сколько можно запросить новый.
      if (failure instanceof ApiError && failure.status === 429 && failure.retryAfter && failure.retryAfter <= 600) {
        router.push({
          pathname: '/code',
          params: { identifier, resendAfter: String(failure.retryAfter), devCode: '' },
        });
      } else {
        setError(failure instanceof ApiError ? failure.message : 'Не удалось отправить код.');
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <FormScreen
      top={<ScreenHeader />}
      footer={<PrimaryButton label="Получить код" onPress={() => void send()} disabled={!canSend} loading={sending} />}>
      <Title>Вход</Title>
      <Subtitle>Отправим одноразовый код. Пароль не нужен — так же войдёшь и на другом телефоне.</Subtitle>

      <View style={styles.tabs}>
        {KINDS.map((option) => {
          const active = option.id === kind;
          return (
            <Pressable
              key={option.id}
              onPress={() => {
                setKind(option.id);
                setValue('');
                setError(null);
              }}
              style={[styles.tab, active && styles.tabActive]}
              accessibilityRole="tab"
              accessibilityState={{ selected: active }}>
              <Text style={[styles.tabText, active && styles.tabTextActive]}>{option.label}</Text>
            </Pressable>
          );
        })}
      </View>

      <TextInput
        value={value}
        onChangeText={(text) => {
          setValue(text);
          setError(null);
        }}
        placeholder={kind === 'phone' ? '+7 999 123-45-67' : 'name@example.com'}
        placeholderTextColor={colors.inkSoft}
        keyboardType={kind === 'phone' ? 'phone-pad' : 'email-address'}
        autoComplete={kind === 'phone' ? 'tel' : 'email'}
        textContentType={kind === 'phone' ? 'telephoneNumber' : 'emailAddress'}
        autoCapitalize="none"
        autoCorrect={false}
        autoFocus
        returnKeyType="go"
        onSubmitEditing={() => canSend && void send()}
        style={styles.input}
        accessibilityLabel={kind === 'phone' ? 'Номер телефона' : 'Адрес почты'}
      />
      {kind === 'phone' && looksLikeEmail(value) ? <ErrorText>Похоже на почту — переключитесь на вкладку «Почта».</ErrorText> : null}
      <ErrorText>{error}</ErrorText>
    </FormScreen>
  );
}

const styles = StyleSheet.create({
  tabs: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  tab: {
    paddingVertical: spacing.sm + 1,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
  },
  tabActive: {
    backgroundColor: colors.ink,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.ink,
  },
  tabTextActive: {
    color: colors.onDark,
  },
  input: {
    height: 56,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    fontSize: 18,
    color: colors.ink,
  },
});

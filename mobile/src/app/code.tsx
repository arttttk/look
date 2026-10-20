import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { TextButton } from '@/components/Buttons';
import { ErrorText, Subtitle, Title } from '@/components/FormText';
import { FormScreen } from '@/components/FormScreen';
import { ScreenHeader } from '@/components/ScreenHeader';
import { ApiError } from '@/lib/api';
import { useAuth } from '@/state/auth';
import { colors, radius, spacing } from '@/theme';

const CODE_LENGTH = 6;

export default function CodeScreen() {
  const params = useLocalSearchParams<{ identifier: string; resendAfter?: string; devCode?: string }>();
  const { requestCode, verifyCode } = useAuth();

  const identifier = params.identifier ?? '';
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(Number(params.resendAfter) || 60);
  const [devCode, setDevCode] = useState(params.devCode || null);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setTimeout(() => setSecondsLeft((seconds) => seconds - 1), 1000);
    return () => clearTimeout(timer);
  }, [secondsLeft]);

  const submit = async (value: string) => {
    setVerifying(true);
    setError(null);
    try {
      // Успех переключит приложение дальше само (состояние входа поменяется, экран закроется).
      await verifyCode(identifier, value);
    } catch (failure) {
      setError(failure instanceof ApiError ? failure.message : 'Не удалось проверить код.');
      setCode('');
      setVerifying(false);
    }
  };

  const change = (text: string) => {
    const digits = text.replace(/\D/g, '').slice(0, CODE_LENGTH);
    setCode(digits);
    setError(null);
    if (digits.length === CODE_LENGTH && !verifying) void submit(digits);
  };

  const resend = async () => {
    setError(null);
    try {
      const issued = await requestCode(identifier);
      setSecondsLeft(issued.resend_after);
      setDevCode(issued.dev_code);
    } catch (failure) {
      if (failure instanceof ApiError && failure.retryAfter) setSecondsLeft(failure.retryAfter);
      setError(failure instanceof ApiError ? failure.message : 'Не удалось отправить код.');
    }
  };

  return (
    <FormScreen top={<ScreenHeader />}>
      <Title>Введите код</Title>
      <Subtitle>{`Мы отправили код на ${identifier}. Он действует 5 минут.`}</Subtitle>

      <TextInput
        value={code}
        onChangeText={change}
        editable={!verifying}
        placeholder="——————"
        placeholderTextColor={colors.line}
        keyboardType="number-pad"
        autoComplete="sms-otp"
        textContentType="oneTimeCode"
        maxLength={CODE_LENGTH}
        autoFocus
        style={styles.input}
        accessibilityLabel="Код из сообщения"
      />
      <Text style={styles.status}>{verifying ? 'Проверяем…' : ' '}</Text>
      <ErrorText>{error}</ErrorText>

      {devCode ? (
        <View style={styles.dev}>
          <Text style={styles.devText}>Режим разработки. Код: {devCode}</Text>
          <Pressable onPress={() => change(devCode)} hitSlop={8} accessibilityRole="button">
            <Text style={styles.devAction}>Подставить</Text>
          </Pressable>
        </View>
      ) : null}

      <View style={styles.resend}>
        {secondsLeft > 0 ? (
          <Text style={styles.wait}>Отправить код ещё раз можно через {secondsLeft} с</Text>
        ) : (
          <TextButton label="Отправить код ещё раз" onPress={() => void resend()} />
        )}
      </View>
    </FormScreen>
  );
}

const styles = StyleSheet.create({
  input: {
    height: 64,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    fontSize: 30,
    fontWeight: '800',
    letterSpacing: 10,
    textAlign: 'center',
    color: colors.ink,
  },
  status: {
    fontSize: 13,
    color: colors.inkSoft,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  dev: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.chip,
  },
  devText: {
    fontSize: 13,
    color: colors.ink,
  },
  devAction: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.ink,
  },
  resend: {
    alignItems: 'center',
    marginTop: spacing.lg,
  },
  wait: {
    fontSize: 14,
    color: colors.inkSoft,
  },
});

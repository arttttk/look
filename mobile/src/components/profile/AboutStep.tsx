import { StyleSheet, Text, TextInput, View } from 'react-native';

import { MAX_NAME_LENGTH } from '@/lib/profileForm';
import { colors, radius, spacing } from '@/theme';

type Props = {
  name: string;
  birthYear: string;
  onChangeName: (value: string) => void;
  onChangeBirthYear: (value: string) => void;
  birthYearError?: string | null;
};

export function AboutStep({ name, birthYear, onChangeName, onChangeBirthYear, birthYearError }: Props) {
  return (
    <View style={styles.wrap}>
      <View style={styles.field}>
        <Text style={styles.label}>Как к тебе обращаться?</Text>
        <TextInput
          value={name}
          onChangeText={onChangeName}
          placeholder="Имя"
          placeholderTextColor={colors.inkSoft}
          maxLength={MAX_NAME_LENGTH}
          autoCapitalize="words"
          autoComplete="given-name"
          returnKeyType="next"
          style={styles.input}
        />
      </View>

      <View style={styles.field}>
        <Text style={styles.label}>Год рождения</Text>
        <TextInput
          value={birthYear}
          onChangeText={(text) => onChangeBirthYear(text.replace(/\D/g, '').slice(0, 4))}
          placeholder="Например, 1998"
          placeholderTextColor={colors.inkSoft}
          keyboardType="number-pad"
          maxLength={4}
          returnKeyType="done"
          style={[styles.input, birthYearError ? styles.inputError : null]}
        />
        {birthYearError ? <Text style={styles.error}>{birthYearError}</Text> : null}
        <Text style={styles.hint}>Необязательно. Помогает подбирать вещи по возрасту.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.lg,
  },
  field: {
    gap: spacing.sm,
  },
  label: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.ink,
  },
  input: {
    height: 52,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    fontSize: 16,
    color: colors.ink,
  },
  inputError: {
    borderColor: colors.like,
  },
  error: {
    fontSize: 13,
    color: colors.like,
  },
  hint: {
    fontSize: 13,
    color: colors.inkSoft,
  },
});

import { StyleSheet, Text, View } from 'react-native';

import { OptionRow } from '@/components/OptionRow';
import { type Budget, budgetOptions } from '@/data/profile';
import { colors, spacing } from '@/theme';

type Props = {
  value: Budget | null;
  onChange: (value: Budget | null) => void;
};

export function BudgetStep({ value, onChange }: Props) {
  return (
    <View style={styles.list}>
      {budgetOptions.map((option) => (
        <OptionRow
          key={option.id}
          title={option.title}
          description={option.description}
          selected={option.id === value}
          // Повторное нажатие снимает выбор: бюджет необязателен.
          onPress={() => onChange(option.id === value ? null : option.id)}
        />
      ))}
      <Text style={styles.hint}>Подбираем образы так, чтобы вещи не выходили за этот потолок.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  list: {
    gap: spacing.sm + 2,
  },
  hint: {
    fontSize: 13,
    color: colors.inkSoft,
    marginTop: spacing.xs,
  },
});

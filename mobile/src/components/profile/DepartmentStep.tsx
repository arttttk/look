import { StyleSheet, View } from 'react-native';

import { OptionRow } from '@/components/OptionRow';
import { type Department, departments } from '@/data/taxonomy';
import { spacing } from '@/theme';

type Props = {
  value: Department | null;
  onChange: (value: Department) => void;
};

export function DepartmentStep({ value, onChange }: Props) {
  return (
    <View style={styles.list}>
      {departments.map((option) => (
        <OptionRow
          key={option.id}
          title={option.title}
          description={option.description}
          selected={option.id === value}
          onPress={() => onChange(option.id)}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  list: {
    gap: spacing.sm + 2,
  },
});

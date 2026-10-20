import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { colors, radius, spacing } from '@/theme';

type Props = {
  title: string;
  description?: string;
  selected: boolean;
  onPress: () => void;
};

// Строка выбора одного варианта из списка («для кого», бюджет).
export function OptionRow({ title, description, selected, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.row, selected && styles.rowSelected]}
      accessibilityRole="radio"
      accessibilityState={{ selected }}>
      <View style={styles.text}>
        <Text style={styles.title}>{title}</Text>
        {description ? <Text style={styles.description}>{description}</Text> : null}
      </View>
      <View style={[styles.radio, selected && styles.radioSelected]}>
        {selected ? <Icon name="check" size={14} color={colors.onDark} strokeWidth={3} /> : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 2,
    borderColor: colors.line,
    backgroundColor: colors.surface,
  },
  rowSelected: {
    borderColor: colors.ink,
  },
  text: {
    flex: 1,
  },
  title: {
    fontSize: 17,
    fontWeight: '800',
    color: colors.ink,
  },
  description: {
    fontSize: 13,
    color: colors.inkSoft,
    marginTop: 2,
  },
  radio: {
    width: 24,
    height: 24,
    borderRadius: radius.pill,
    borderWidth: 2,
    borderColor: colors.line,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioSelected: {
    backgroundColor: colors.ink,
    borderColor: colors.ink,
  },
});

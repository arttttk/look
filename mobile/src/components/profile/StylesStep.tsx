import { StyleSheet, useWindowDimensions, View } from 'react-native';

import { StyleCard } from '@/components/StyleCard';
import { type StyleId, styleOptions } from '@/data/styles';
import { spacing } from '@/theme';

type Props = {
  selected: StyleId[];
  onChange: (value: StyleId[]) => void;
};

export function StylesStep({ selected, onChange }: Props) {
  const { width } = useWindowDimensions();
  const cardWidth = Math.floor((width - spacing.md * 2 - spacing.sm) / 2);

  const toggle = (id: StyleId) =>
    onChange(selected.includes(id) ? selected.filter((style) => style !== id) : [...selected, id]);

  return (
    <View style={styles.grid}>
      {styleOptions.map((option) => (
        <StyleCard
          key={option.id}
          option={option}
          width={cardWidth}
          selected={selected.includes(option.id)}
          onPress={() => toggle(option.id)}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
});

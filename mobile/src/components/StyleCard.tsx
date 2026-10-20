import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Icon } from '@/components/Icon';
import type { StyleOption } from '@/data/styles';
import { colors, radius, spacing } from '@/theme';

type Props = {
  option: StyleOption;
  width: number;
  selected: boolean;
  onPress: () => void;
};

export function StyleCard({ option, width, selected, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.card, { width, backgroundColor: option.color }, selected && styles.selected]}
      accessibilityRole="checkbox"
      accessibilityState={{ checked: selected }}
      accessibilityLabel={`${option.title}. ${option.description}`}>
      <Image source={option.image} contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
      <LinearGradient
        colors={['rgba(0,0,0,0)', 'rgba(0,0,0,0.8)']}
        locations={[0.3, 1]}
        style={StyleSheet.absoluteFill}
      />
      <View style={[styles.check, selected && styles.checkOn]}>
        {selected ? <Icon name="check" size={16} color={colors.ink} strokeWidth={2.5} /> : null}
      </View>
      <Text style={styles.title}>{option.title}</Text>
      <Text style={styles.description} numberOfLines={2}>
        {option.description}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    aspectRatio: 0.9,
    borderRadius: radius.lg,
    overflow: 'hidden',
    borderWidth: 3,
    borderColor: 'transparent',
    padding: spacing.md - 2,
    justifyContent: 'flex-end',
  },
  selected: {
    borderColor: colors.ink,
  },
  check: {
    position: 'absolute',
    top: spacing.sm + 2,
    right: spacing.sm + 2,
    width: 26,
    height: 26,
    borderRadius: radius.pill,
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.7)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkOn: {
    backgroundColor: colors.onDark,
    borderColor: colors.onDark,
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.onDark,
    marginBottom: 2,
  },
  description: {
    fontSize: 12,
    lineHeight: 15,
    color: colors.onDarkSoft,
  },
});

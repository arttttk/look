import { Image } from 'expo-image';
import { type StyleProp, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { isLight } from '@/lib/color';
import type { Piece } from '@/lib/outfits';
import { colorById } from '@/data/taxonomy';

type Props = {
  pieces: Piece[];
  labels?: boolean;
  style?: StyleProp<ViewStyle>;
};

// Коллаж образа из вещей: крупная плитка слева и столбец остальных справа. Пока у вещей
// каталога нет фото, плитка рисуется цветом вещи с подписью; с реальными фото ляжет картинка.
export function LookCollage({ pieces, labels = true, style }: Props) {
  const [first, ...rest] = pieces;

  return (
    <View style={[styles.grid, style]}>
      <View style={styles.cell}>{first ? <Tile piece={first} labels={labels} /> : null}</View>
      <View style={[styles.cell, styles.column]}>
        {rest.map((piece) => (
          <View key={piece.id} style={styles.cell}>
            <Tile piece={piece} labels={labels} />
          </View>
        ))}
      </View>
    </View>
  );
}

export function Tile({ piece, labels = true }: { piece: Piece; labels?: boolean }) {
  const { hex } = colorById(piece.color);

  return (
    <View style={[styles.tile, { backgroundColor: hex }]}>
      {piece.image ? (
        <Image source={piece.image} contentFit="cover" transition={200} style={StyleSheet.absoluteFill} />
      ) : labels ? (
        <Text
          style={[styles.label, { color: isLight(hex) ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.85)' }]}
          numberOfLines={2}>
          {piece.title}
        </Text>
      ) : null}
    </View>
  );
}

const GAP = 3;

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    gap: GAP,
    overflow: 'hidden',
  },
  cell: {
    flex: 1,
  },
  column: {
    gap: GAP,
  },
  tile: {
    flex: 1,
    justifyContent: 'flex-end',
    padding: 8,
    overflow: 'hidden',
  },
  label: {
    fontSize: 11,
    fontWeight: '600',
    lineHeight: 14,
  },
});

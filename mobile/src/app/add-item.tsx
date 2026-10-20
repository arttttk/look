import { Image } from 'expo-image';
import * as ImagePicker from 'expo-image-picker';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Icon } from '@/components/Icon';
import { ScreenHeader } from '@/components/ScreenHeader';
import { type Category, type ColorId, categories, colorById, colorOptions } from '@/data/taxonomy';
import { persistImage } from '@/lib/images';
import { closeScreen } from '@/lib/navigation';
import { useWardrobe } from '@/state/wardrobe';
import { colors, radius, spacing } from '@/theme';

export default function AddItemScreen() {
  const { addItem } = useWardrobe();
  const [uri, setUri] = useState<string | null>(null);
  const [category, setCategory] = useState<Category | null>(null);
  const [color, setColor] = useState<ColorId | null>(null);
  const [title, setTitle] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSave = uri !== null && category !== null && color !== null && !saving;

  const pick = async (source: 'camera' | 'library') => {
    setError(null);
    try {
      if (source === 'camera') {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          setError('Нет доступа к камере. Разрешите его в настройках телефона.');
          return;
        }
      }

      const options: ImagePicker.ImagePickerOptions = { mediaTypes: ['images'], quality: 0.8 };
      const result =
        source === 'camera'
          ? await ImagePicker.launchCameraAsync(options)
          : await ImagePicker.launchImageLibraryAsync(options);

      if (!result.canceled) setUri(result.assets[0].uri);
    } catch {
      setError('Не удалось открыть камеру или галерею. Попробуйте ещё раз.');
    }
  };

  const save = async () => {
    if (!uri || !category || !color) return;

    setSaving(true);
    setError(null);
    try {
      const image = await persistImage(uri);
      addItem({ category, color, title: title.trim(), image });
      closeScreen();
    } catch {
      setError('Не удалось сохранить фото. Попробуйте ещё раз.');
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <ScreenHeader title="Новая вещь" icon="x" />

      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}>
        <Text style={styles.heading}>Фото</Text>
        {uri ? (
          <View>
            <View style={styles.preview}>
              <Image source={uri} contentFit="cover" style={StyleSheet.absoluteFill} />
            </View>
            <View style={styles.row}>
              <SourceButton icon="camera" label="Переснять" onPress={() => void pick('camera')} compact />
              <SourceButton icon="image" label="Другое фото" onPress={() => void pick('library')} compact />
            </View>
          </View>
        ) : (
          <View style={styles.row}>
            <SourceButton icon="camera" label="Сфотографировать" onPress={() => void pick('camera')} />
            <SourceButton icon="image" label="Из галереи" onPress={() => void pick('library')} />
          </View>
        )}

        <Text style={styles.heading}>Категория</Text>
        <View style={styles.chips}>
          {categories.map((option) => {
            const active = option.id === category;
            return (
              <Pressable
                key={option.id}
                onPress={() => setCategory(option.id)}
                style={[styles.chip, active && styles.chipActive]}
                accessibilityRole="radio"
                accessibilityState={{ selected: active }}>
                <Text style={[styles.chipText, active && styles.chipTextActive]}>{option.title}</Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.heading}>Цвет{color ? ` · ${colorById(color).title}` : ''}</Text>
        <View style={styles.swatches}>
          {colorOptions.map((option) => {
            const active = option.id === color;
            return (
              <Pressable
                key={option.id}
                onPress={() => setColor(option.id)}
                style={[styles.swatchRing, active && styles.swatchRingActive]}
                accessibilityRole="radio"
                accessibilityState={{ selected: active }}
                accessibilityLabel={option.title}>
                <View style={[styles.swatch, { backgroundColor: option.hex }]} />
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.heading}>Название</Text>
        <TextInput
          value={title}
          onChangeText={setTitle}
          placeholder="Необязательно, например «Любимая куртка»"
          placeholderTextColor={colors.inkSoft}
          maxLength={40}
          returnKeyType="done"
          style={styles.input}
        />

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Pressable
          onPress={() => void save()}
          disabled={!canSave}
          style={({ pressed }) => [styles.save, !canSave && styles.saveDisabled, pressed && styles.pressed]}
          accessibilityRole="button"
          accessibilityState={{ disabled: !canSave }}>
          <Text style={[styles.saveText, !canSave && styles.saveTextDisabled]}>
            {saving ? 'Сохраняем…' : 'Добавить в гардероб'}
          </Text>
        </Pressable>
        {!uri || !category || !color ? (
          <Text style={styles.hint}>Нужны фото, категория и цвет — по ним мы подбираем образы.</Text>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

type SourceProps = {
  icon: 'camera' | 'image';
  label: string;
  onPress: () => void;
  compact?: boolean;
};

function SourceButton({ icon, label, onPress, compact }: SourceProps) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.source, compact && styles.sourceCompact, pressed && styles.pressed]}
      accessibilityRole="button">
      <Icon name={icon} size={compact ? 18 : 26} color={colors.ink} />
      <Text style={styles.sourceText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  heading: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.ink,
    marginTop: spacing.lg,
    marginBottom: spacing.sm + 2,
  },
  row: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  preview: {
    aspectRatio: 1,
    borderRadius: radius.lg,
    overflow: 'hidden',
    backgroundColor: colors.chip,
    marginBottom: spacing.sm,
  },
  source: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.lg,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
  },
  sourceCompact: {
    flexDirection: 'row',
    paddingVertical: spacing.sm + 4,
  },
  sourceText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.ink,
  },
  pressed: {
    opacity: 0.8,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  chip: {
    paddingVertical: spacing.sm + 2,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    backgroundColor: colors.chip,
  },
  chipActive: {
    backgroundColor: colors.ink,
  },
  chipText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.ink,
  },
  chipTextActive: {
    color: colors.onDark,
  },
  swatches: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm + 2,
  },
  swatchRing: {
    width: 46,
    height: 46,
    borderRadius: radius.pill,
    borderWidth: 2,
    borderColor: 'transparent',
    alignItems: 'center',
    justifyContent: 'center',
  },
  swatchRingActive: {
    borderColor: colors.ink,
  },
  swatch: {
    width: 34,
    height: 34,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.12)',
  },
  input: {
    height: 50,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    fontSize: 15,
    color: colors.ink,
  },
  error: {
    fontSize: 14,
    color: colors.like,
    marginTop: spacing.md,
  },
  save: {
    marginTop: spacing.lg,
    height: 52,
    borderRadius: radius.pill,
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveDisabled: {
    backgroundColor: colors.chip,
  },
  saveText: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onDark,
  },
  saveTextDisabled: {
    color: colors.inkSoft,
  },
  hint: {
    fontSize: 13,
    color: colors.inkSoft,
    textAlign: 'center',
    marginTop: spacing.sm + 2,
  },
});

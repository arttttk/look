import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { Icon } from '@/components/Icon';
import { type City, type Location, locationFromCity } from '@/data/profile';
import { ApiError } from '@/lib/api';
import { detectLocation, LocationUnavailable, searchCities } from '@/lib/geo';
import { colors, radius, spacing } from '@/theme';

type Props = {
  value: Location | null;
  onChange: (value: Location | null) => void;
};

const SEARCH_DELAY_MS = 350;

export function LocationStep({ value, onChange }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<City[]>([]);
  const [searching, setSearching] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  // Поиск с задержкой: не дёргаем сервер на каждую букву, а ответы на устаревшие запросы отбрасываем.
  useEffect(() => {
    const text = query.trim();
    const id = ++requestId.current;
    if (text.length < 2) return;

    const timer = setTimeout(() => {
      setSearching(true);
      setError(null);
      searchCities(text)
        .then((cities) => id === requestId.current && setResults(cities))
        .catch((failure: unknown) => {
          if (id !== requestId.current) return;
          setResults([]);
          setError(failure instanceof ApiError ? failure.message : 'Не удалось найти город.');
        })
        .finally(() => id === requestId.current && setSearching(false));
    }, SEARCH_DELAY_MS);

    return () => clearTimeout(timer);
  }, [query]);

  const detect = async () => {
    setDetecting(true);
    setError(null);
    try {
      onChange(await detectLocation());
      setQuery('');
      setResults([]);
    } catch (failure) {
      setError(failure instanceof LocationUnavailable ? failure.message : 'Не удалось определить место.');
    } finally {
      setDetecting(false);
    }
  };

  const choose = (city: City) => {
    onChange(locationFromCity(city));
    setQuery('');
    setResults([]);
  };

  const visibleResults = query.trim().length >= 2 ? results : [];

  return (
    <View style={styles.wrap}>
      {value ? (
        <View style={styles.selected}>
          <Icon name="check" size={18} color={colors.onDark} strokeWidth={2.5} />
          <Text style={styles.selectedText} numberOfLines={1}>
            {value.city}, {value.country_code}
          </Text>
          <Pressable onPress={() => onChange(null)} hitSlop={8} accessibilityRole="button" accessibilityLabel="Убрать город">
            <Icon name="x" size={18} color={colors.onDark} />
          </Pressable>
        </View>
      ) : null}

      <Pressable
        onPress={() => void detect()}
        disabled={detecting}
        style={({ pressed }) => [styles.detect, pressed && styles.pressed]}
        accessibilityRole="button">
        {detecting ? <ActivityIndicator color={colors.ink} /> : <Icon name="scan" size={20} color={colors.ink} />}
        <Text style={styles.detectText}>{detecting ? 'Определяем…' : 'Определить автоматически'}</Text>
      </Pressable>

      <Text style={styles.or}>или найдите свой город</Text>

      <TextInput
        value={query}
        onChangeText={setQuery}
        placeholder="Например, Казань"
        placeholderTextColor={colors.inkSoft}
        autoCorrect={false}
        returnKeyType="search"
        style={styles.input}
      />

      {searching ? <ActivityIndicator style={styles.spinner} color={colors.inkSoft} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {visibleResults.map((city) => (
        <Pressable
          key={`${city.city}-${city.lat}-${city.lon}`}
          onPress={() => choose(city)}
          style={({ pressed }) => [styles.result, pressed && styles.pressed]}
          accessibilityRole="button">
          <Text style={styles.resultTitle}>{city.city}</Text>
          <Text style={styles.resultSub} numberOfLines={1}>
            {[city.region, city.country].filter(Boolean).join(', ')}
          </Text>
        </Pressable>
      ))}

      <Text style={styles.hint}>По городу мы узнаём погоду и подбираем образы под неё. Точное место не сохраняется.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.sm + 2,
  },
  selected: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.ink,
  },
  selectedText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '700',
    color: colors.onDark,
  },
  detect: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    height: 52,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.ink,
  },
  pressed: {
    opacity: 0.7,
  },
  detectText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.ink,
  },
  or: {
    fontSize: 13,
    color: colors.inkSoft,
    textAlign: 'center',
    marginVertical: spacing.xs,
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
  spinner: {
    marginVertical: spacing.sm,
  },
  error: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.like,
  },
  result: {
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.ink,
  },
  resultSub: {
    fontSize: 13,
    color: colors.inkSoft,
    marginTop: 2,
  },
  hint: {
    fontSize: 13,
    lineHeight: 18,
    color: colors.inkSoft,
    marginTop: spacing.sm,
  },
});

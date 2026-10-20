import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useRef, useState } from 'react';

// Состояние, которое переживает перезапуск приложения. `initial` и `parse` должны быть
// константами уровня модуля: parse превращает «что угодно из хранилища» в валидное значение.
export function usePersisted<T>(key: string, initial: T, parse: (raw: unknown) => T) {
  const [value, setValue] = useState(initial);
  const [ready, setReady] = useState(false);
  const latest = useRef(initial);

  useEffect(() => {
    let active = true;

    AsyncStorage.getItem(key)
      .then((raw) => (raw ? parse(JSON.parse(raw)) : initial))
      .catch(() => initial)
      .then((loaded) => {
        if (!active) return;
        latest.current = loaded;
        setValue(loaded);
        setReady(true);
      });

    return () => {
      active = false;
    };
  }, [key, initial, parse]);

  const update = useCallback(
    (updater: (prev: T) => T) => {
      const next = updater(latest.current);
      latest.current = next;
      setValue(next);
      AsyncStorage.setItem(key, JSON.stringify(next)).catch(() => {
        // Не сохранилось — данные останутся только до перезапуска приложения.
      });
    },
    [key],
  );

  return { value, ready, update };
}

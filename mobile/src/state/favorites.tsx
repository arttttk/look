import { createContext, type ReactNode, useContext, useMemo } from 'react';

import { useProfile } from '@/state/profile';
import { usePersisted } from '@/state/usePersisted';

type FavoritesContextValue = {
  // id образов, последние добавленные — первыми.
  ids: string[];
  isFavorite: (id: string) => boolean;
  toggle: (id: string) => void;
};

const initialIds: string[] = [];

const parseIds = (raw: unknown): string[] =>
  Array.isArray(raw) ? raw.filter((entry): entry is string => typeof entry === 'string') : [];

const FavoritesContext = createContext<FavoritesContextValue | null>(null);

export function FavoritesProvider({ children }: { children: ReactNode }) {
  // Данные на устройстве хранятся отдельно для каждого пользователя.
  const { profile } = useProfile();
  const { value: ids, update } = usePersisted(`look.favorites.v1.${profile.id}`, initialIds, parseIds);

  const value = useMemo<FavoritesContextValue>(
    () => ({
      ids,
      isFavorite: (id) => ids.includes(id),
      toggle: (id) => update((prev) => (prev.includes(id) ? prev.filter((entry) => entry !== id) : [id, ...prev])),
    }),
    [ids, update],
  );

  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}

export function useFavorites() {
  const value = useContext(FavoritesContext);
  if (!value) throw new Error('useFavorites must be used inside FavoritesProvider');
  return value;
}

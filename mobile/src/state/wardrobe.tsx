import { createContext, type ReactNode, useContext, useMemo } from 'react';

import { newItemId, parseWardrobe, type WardrobeItem } from '@/data/wardrobe';
import { removeImage } from '@/lib/images';
import { useProfile } from '@/state/profile';
import { usePersisted } from '@/state/usePersisted';

type NewItem = Omit<WardrobeItem, 'id' | 'createdAt'>;

type WardrobeContextValue = {
  ready: boolean;
  items: WardrobeItem[];
  addItem: (input: NewItem) => WardrobeItem;
  removeItem: (id: string) => void;
};

const initialItems: WardrobeItem[] = [];

const WardrobeContext = createContext<WardrobeContextValue | null>(null);

export function WardrobeProvider({ children }: { children: ReactNode }) {
  // Данные на устройстве хранятся отдельно для каждого пользователя.
  const { profile } = useProfile();
  const { value: items, ready, update } = usePersisted(`look.wardrobe.v1.${profile.id}`, initialItems, parseWardrobe);

  const value = useMemo<WardrobeContextValue>(
    () => ({
      ready,
      items,
      addItem: (input) => {
        const item: WardrobeItem = { ...input, id: newItemId(), createdAt: Date.now() };
        update((prev) => [item, ...prev]);
        return item;
      },
      removeItem: (id) => {
        const item = items.find((entry) => entry.id === id);
        if (item) removeImage(item.image);
        update((prev) => prev.filter((entry) => entry.id !== id));
      },
    }),
    [ready, items, update],
  );

  return <WardrobeContext.Provider value={value}>{children}</WardrobeContext.Provider>;
}

export function useWardrobe() {
  const value = useContext(WardrobeContext);
  if (!value) throw new Error('useWardrobe must be used inside WardrobeProvider');
  return value;
}

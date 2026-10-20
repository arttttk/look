import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { fetchFeedPage } from '@/data/feed';
import type { StyleId } from '@/data/styles';
import type { Department } from '@/data/taxonomy';
import type { Outfit } from '@/lib/outfits';

export function useFeed(department: Department, styles: StyleId[]) {
  const [outfits, setOutfits] = useState<Outfit[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const cursor = useRef<number | null>(0);
  const inFlight = useRef(false);
  // Растёт при каждой смене профиля: ответы от устаревших запросов отбрасываются.
  const generation = useRef(0);

  const stylesKey = styles.join(',');
  const profileKey = `${department}|${stylesKey}`;
  const profile = useMemo(
    () => ({ department, styles: stylesKey ? (stylesKey.split(',') as StyleId[]) : [] }),
    [department, stylesKey],
  );

  const loadMore = useCallback(async () => {
    if (inFlight.current || cursor.current === null) return;

    const current = generation.current;
    inFlight.current = true;
    setLoading(true);
    try {
      const page = await fetchFeedPage(cursor.current, profile);
      if (current !== generation.current) return;

      cursor.current = page.nextCursor;
      setHasMore(page.nextCursor !== null);
      setOutfits((prev) => [...prev, ...page.items]);
    } finally {
      if (current === generation.current) {
        inFlight.current = false;
        setLoading(false);
      }
    }
  }, [profile]);

  // При смене профиля лента начинается заново: список сбрасываем прямо при рендере...
  const [loadedKey, setLoadedKey] = useState(profileKey);
  if (loadedKey !== profileKey) {
    setLoadedKey(profileKey);
    setOutfits([]);
    setHasMore(true);
  }

  // ...а курсор и первую страницу — в эффекте.
  useEffect(() => {
    generation.current += 1;
    cursor.current = 0;
    inFlight.current = false;
    void loadMore();
  }, [loadMore]);

  return { outfits, loading, hasMore, loadMore };
}

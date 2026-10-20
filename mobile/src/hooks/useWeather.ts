import { useEffect, useState } from 'react';

import type { Weather } from '@/data/profile';
import { api } from '@/lib/api';
import { useProfile } from '@/state/profile';

const REFRESH_MS = 15 * 60 * 1000;

// Погода в городе пользователя. Нет города или сервис недоступен — null: интерфейс обходится без неё.
export function useWeather(): Weather | null {
  const { profile } = useProfile();
  const key = profile.location ? `${profile.location.lat},${profile.location.lon}` : null;
  const [state, setState] = useState<{ key: string | null; weather: Weather | null }>({ key: null, weather: null });

  useEffect(() => {
    if (!key) return;

    let active = true;
    const load = () => {
      api
        .get<Weather>('/weather')
        .then((weather) => active && setState({ key, weather }))
        .catch(() => active && setState({ key, weather: null }));
    };

    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [key]);

  // Ответ относится к тому месту, для которого запрашивали: после смены города старая погода не показывается.
  return state.key === key ? state.weather : null;
}

import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { EMPTY_PROFILE, type Profile, type ProfilePatch } from '@/data/profile';
import type { StyleId } from '@/data/styles';
import type { Department } from '@/data/taxonomy';
import { api, ApiError } from '@/lib/api';
import { useAuth } from '@/state/auth';

type ProfileStatus = 'idle' | 'loading' | 'ready' | 'error';

type ProfileContextValue = {
  status: ProfileStatus;
  ready: boolean;
  error: string | null;
  profile: Profile;
  reload: () => void;
  // Меняет профиль на экране сразу, а на сервере — следом. Если сервер отказал, откатывает и бросает ApiError.
  update: (patch: ProfilePatch) => Promise<void>;
  completeOnboarding: (choice: { department: Department; styles: StyleId[] } & ProfilePatch) => Promise<void>;
};

const ProfileContext = createContext<ProfileContextValue | null>(null);

export function ProfileProvider({ children }: { children: ReactNode }) {
  const { status: authStatus } = useAuth();
  const signedIn = authStatus === 'signedIn';

  const [status, setStatus] = useState<ProfileStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile>(EMPTY_PROFILE);
  const [attempt, setAttempt] = useState(0);
  const latest = useRef(profile);

  // Вход и выход начинают историю профиля заново: сбрасываем состояние прямо при рендере...
  const [wasSignedIn, setWasSignedIn] = useState(signedIn);
  if (wasSignedIn !== signedIn) {
    setWasSignedIn(signedIn);
    setProfile(EMPTY_PROFILE);
    setError(null);
    setStatus(signedIn ? 'loading' : 'idle');
  }

  useEffect(() => {
    latest.current = profile;
  }, [profile]);

  const apply = useCallback((next: Profile) => {
    latest.current = next;
    setProfile(next);
  }, []);

  // ...а профиль с сервера подгружаем эффектом.
  useEffect(() => {
    if (!signedIn) return;

    let active = true;

    api
      .get<Profile>('/me')
      .then((loaded) => {
        if (!active) return;
        apply(loaded);
        setStatus('ready');
      })
      .catch((failure: unknown) => {
        // 401 уже обработал клиент API (выход на экран входа); тут остаются сбои сети и сервера.
        if (!active) return;
        setError(failure instanceof ApiError ? failure.message : 'Не удалось загрузить профиль.');
        setStatus('error');
      });

    return () => {
      active = false;
    };
  }, [signedIn, attempt, apply]);

  const reload = useCallback(() => {
    setError(null);
    setStatus('loading');
    setAttempt((count) => count + 1);
  }, []);

  const update = useCallback(
    async (patch: ProfilePatch) => {
      const before = latest.current;
      apply({ ...before, ...patch });
      try {
        apply(await api.patch<Profile>('/me', patch));
      } catch (failure) {
        apply(before);
        throw failure;
      }
    },
    [apply],
  );

  const completeOnboarding = useCallback(
    (choice: { department: Department; styles: StyleId[] } & ProfilePatch) => update({ ...choice, onboarded: true }),
    [update],
  );

  const value = useMemo<ProfileContextValue>(
    () => ({
      status,
      ready: status === 'ready',
      error,
      profile,
      reload,
      update,
      completeOnboarding,
    }),
    [status, error, profile, reload, update, completeOnboarding],
  );

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export function useProfile() {
  const value = useContext(ProfileContext);
  if (!value) throw new Error('useProfile must be used inside ProfileProvider');
  return value;
}

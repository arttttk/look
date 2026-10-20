import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import type { CodeSent, TokenResponse } from '@/data/profile';
import { api, setAuthToken, setUnauthorizedHandler } from '@/lib/api';
import { clearToken, readToken, saveToken } from '@/lib/tokenStore';

type AuthStatus = 'loading' | 'signedOut' | 'signedIn';

type AuthContextValue = {
  status: AuthStatus;
  requestCode: (identifier: string) => Promise<CodeSent>;
  verifyCode: (identifier: string, code: string) => Promise<TokenResponse>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');

  const forget = useCallback(async () => {
    setAuthToken(null);
    await clearToken();
    setStatus('signedOut');
  }, []);

  // Токен, сохранённый с прошлого запуска. Действителен ли он, выяснит первый запрос профиля:
  // если нет — клиент API сам вернёт нас на вход (см. setUnauthorizedHandler).
  useEffect(() => {
    let active = true;

    readToken().then((token) => {
      if (!active) return;
      if (token) {
        setAuthToken(token);
        setStatus('signedIn');
      } else {
        setStatus('signedOut');
      }
    });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => void forget());
    return () => setUnauthorizedHandler(null);
  }, [forget]);

  const requestCode = useCallback(
    (identifier: string) => api.post<CodeSent>('/auth/code', { identifier }, { auth: false }),
    [],
  );

  const verifyCode = useCallback(async (identifier: string, code: string) => {
    const result = await api.post<TokenResponse>('/auth/verify', { identifier, code }, { auth: false });
    await saveToken(result.access_token);
    setAuthToken(result.access_token);
    setStatus('signedIn');
    return result;
  }, []);

  const signOut = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Сервер недоступен или токен уже недействителен — локально выходим в любом случае.
    }
    await forget();
  }, [forget]);

  const value = useMemo(
    () => ({ status, requestCode, verifyCode, signOut }),
    [status, requestCode, verifyCode, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}

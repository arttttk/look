import { API_URL } from '@/lib/config';

export class ApiError extends Error {
  constructor(
    public readonly status: number, // 0 — до сервера не достучались
    message: string,
    public readonly retryAfter?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get isNetwork() {
    return this.status === 0;
  }
}

const TIMEOUT_MS = 10_000;

let authToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

// Сессия умерла (токен отозван или просрочен): приложение должно вернуть человека на вход.
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

// FastAPI отдаёт detail строкой (наши ошибки) или списком (проверка формы запроса).
function messageFrom(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    if (first?.msg) return first.msg;
  }
  return status >= 500 ? 'Сервер временно недоступен. Попробуйте позже.' : 'Не удалось выполнить запрос.';
}

type Options = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE' | 'PUT';
  body?: unknown;
  query?: Record<string, string | number | undefined>;
  // Запросы без токена (вход по коду) не должны выкидывать человека при 401.
  auth?: boolean;
};

export async function request<T>(path: string, { method = 'GET', body, query, auth = true }: Options = {}): Promise<T> {
  const params = Object.entries(query ?? {}).filter(([, value]) => value !== undefined);
  const search = params.length > 0 ? `?${new URLSearchParams(params.map(([k, v]) => [k, String(v)]))}` : '';

  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && authToken) headers.Authorization = `Bearer ${authToken}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}${search}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch {
    throw new ApiError(0, 'Нет соединения с сервером. Проверьте интернет и попробуйте ещё раз.');
  } finally {
    clearTimeout(timer);
  }

  if (response.status === 204) return undefined as T;

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    // Пустое или не-JSON тело: сообщение возьмём из статуса.
  }

  if (!response.ok) {
    if (response.status === 401 && auth) onUnauthorized?.();
    const retryAfter = Number(response.headers.get('Retry-After')) || undefined;
    throw new ApiError(response.status, messageFrom(payload, response.status), retryAfter);
  }
  return payload as T;
}

export const api = {
  get: <T>(path: string, query?: Options['query']) => request<T>(path, { query }),
  post: <T>(path: string, body?: unknown, options?: Pick<Options, 'auth'>) =>
    request<T>(path, { method: 'POST', body: body ?? {}, ...options }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body }),
};

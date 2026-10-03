// HTTP-клиент REST API и хранение сессии.
const TOKEN_KEY = 'salary.token';
const USER_KEY = 'salary.user';

export const session = {
  get token() { return localStorage.getItem(TOKEN_KEY); },
  get user() {
    try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; }
  },
  save(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  get isAdmin() { return this.user?.role === 'admin'; },
};

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function errorMessage(body, status) {
  const detail = body?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(d => d.msg).join('; ');
  return `Ошибка ${status}`;
}

export async function api(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && session.token) headers.Authorization = `Bearer ${session.token}`;

  const response = await fetch(`/api${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && auth) {
      session.clear();
      location.hash = '#/login';
    }
    throw new ApiError(response.status, errorMessage(data, response.status));
  }
  return data;
}

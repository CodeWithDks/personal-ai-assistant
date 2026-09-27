import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const TOKEN_KEY = 'pai_token';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const AUTH_EXPIRED_EVENT = 'pai:auth-expired';

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }
    return Promise.reject(error);
  }
);

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<any>;
    if (err.code === 'ECONNABORTED') return 'Request timed out. Try again.';
    if (!err.response) {
      return `Couldn't reach the backend at ${API_BASE_URL}. Is it running?`;
    }
    const detail = err.response.data?.detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d: any) => `${(d.loc || []).join('.')}: ${d.msg ?? d}`)
        .join('; ');
    }
    if (typeof detail === 'string') return detail;
    return `${err.response.status}: ${err.response.statusText}`;
  }
  return 'Something went wrong.';
}

export { API_BASE_URL, TOKEN_KEY };

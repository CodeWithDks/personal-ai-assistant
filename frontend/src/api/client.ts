import axios, { AxiosError } from 'axios';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const TOKEN_KEY = 'pai_token';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Attach the bearer token (if we have one) to every outgoing request.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A 401 anywhere in the app means the token is dead. We clear it and
// broadcast a DOM event so AuthContext (which owns React state) can
// react, without this axios-layer file needing to import React.
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

/**
 * Turns any axios error into a single readable string — mirrors the
 * error-normalizing logic from the original Streamlit api_request,
 * including FastAPI/Pydantic's list-of-dicts validation errors.
 */
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

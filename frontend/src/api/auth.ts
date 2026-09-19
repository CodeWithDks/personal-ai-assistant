import { apiClient, getErrorMessage } from './client';
import type { ApiResult, AuthResponse } from '../types';

export async function login(email: string, password: string): Promise<ApiResult<AuthResponse>> {
  try {
    // NOTE: FastAPI's OAuth2PasswordRequestForm expects form-encoded
    // data (username/password), not JSON — same gotcha as the
    // original Streamlit client.
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const { data } = await apiClient.post<AuthResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function register(email: string, password: string): Promise<ApiResult<unknown>> {
  try {
    const { data } = await apiClient.post('/auth/register', { email, password });
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

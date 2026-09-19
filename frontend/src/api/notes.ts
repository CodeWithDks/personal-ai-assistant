import { apiClient, getErrorMessage } from './client';
import type { ApiResult, Note } from '../types';

export async function getNotes(limit = 100, offset = 0): Promise<ApiResult<Note[]>> {
  try {
    const { data } = await apiClient.get<Note[]>('/notes/', { params: { limit, offset } });
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function searchNotes(params: {
  keyword?: string;
  limit?: number;
  offset?: number;
}): Promise<ApiResult<Note[]>> {
  try {
    const { data } = await apiClient.get<Note[]>('/notes/search', { params });
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function createNote(input: { title?: string; content: string }): Promise<ApiResult<Note>> {
  try {
    const body: Record<string, unknown> = { content: input.content };
    if (input.title) body.title = input.title;
    const { data } = await apiClient.post<Note>('/notes/', body);
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function updateNote(
  id: number,
  fields: Partial<Pick<Note, 'title' | 'content'>>
): Promise<ApiResult<Note | null>> {
  const body = Object.fromEntries(
    Object.entries(fields).filter(([, v]) => v !== undefined && v !== null)
  );
  if (Object.keys(body).length === 0) return { ok: true, data: null };
  try {
    const { data } = await apiClient.put<Note>(`/notes/${id}`, body);
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function deleteNote(id: number): Promise<ApiResult<null>> {
  try {
    await apiClient.delete(`/notes/${id}`);
    return { ok: true, data: null };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

import { apiClient, getErrorMessage } from './client';
import type { ApiResult, Priority, Task, TaskStatus } from '../types';

export async function getTasks(limit = 100, offset = 0): Promise<ApiResult<Task[]>> {
  try {
    const { data } = await apiClient.get<Task[]>('/tasks/', { params: { limit, offset } });
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function searchTasks(params: {
  keyword?: string;
  status?: TaskStatus;
  priority?: Priority;
  limit?: number;
  offset?: number;
}): Promise<ApiResult<Task[]>> {
  try {
    const { data } = await apiClient.get<Task[]>('/tasks/search', { params });
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function createTask(input: {
  title: string;
  description?: string;
  priority: Priority;
  due_date?: string | null;
}): Promise<ApiResult<Task>> {
  try {
    const body: Record<string, unknown> = { title: input.title, priority: input.priority };
    if (input.description) body.description = input.description;
    if (input.due_date) body.due_date = input.due_date;
    const { data } = await apiClient.post<Task>('/tasks/', body);
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function updateTask(
  id: number,
  fields: Partial<Pick<Task, 'title' | 'priority' | 'status' | 'description' | 'due_date'>>
): Promise<ApiResult<Task | null>> {
  // Only send keys that are actually set — skips the request entirely
  // when nothing changed, instead of firing a pointless PUT.
  const body = Object.fromEntries(
    Object.entries(fields).filter(([, v]) => v !== undefined && v !== null)
  );
  if (Object.keys(body).length === 0) return { ok: true, data: null };
  try {
    const { data } = await apiClient.put<Task>(`/tasks/${id}`, body);
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function deleteTask(id: number): Promise<ApiResult<null>> {
  try {
    await apiClient.delete(`/tasks/${id}`);
    return { ok: true, data: null };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

import { useCallback, useEffect, useMemo, useState } from 'react';
import { createTask, deleteTask, getTasks, searchTasks, updateTask } from '../api/tasks';
import type { Priority, Task, TaskStatus } from '../types';

const PAGE_SIZE = 10;
const PRIORITY_ORDER: Record<Priority, number> = { high: 0, medium: 1, low: 2 };

export type SortOption = 'due' | 'priority' | 'newest';

/**
 * Owns all task state: fetching, filtering, sorting, pagination, and
 * mutation (create/edit/delete/bulk). Components just render what
 * this hook gives them — mirrors how the original Streamlit
 * render_tasks_tab() function centralized this logic, but split into
 * a reusable hook instead of one large render function.
 */
export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [priorityFilter, setPriorityFilter] = useState<Priority | 'all'>('all');
  const [sortBy, setSortBy] = useState<SortOption>('due');
  const [page, setPage] = useState(0);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    const usingSearch = !!keyword || statusFilter !== 'all' || priorityFilter !== 'all';
    const res = usingSearch
      ? await searchTasks({
          keyword: keyword || undefined,
          status: statusFilter === 'all' ? undefined : statusFilter,
          priority: priorityFilter === 'all' ? undefined : priorityFilter,
        })
      : await getTasks();
    setLoading(false);
    if (res.ok) setTasks(res.data);
    else setError(res.error);
  }, [keyword, statusFilter, priorityFilter]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const sortedTasks = useMemo(() => {
    const copy = [...tasks];
    if (sortBy === 'due') {
      return copy.sort((a, b) => {
        if (!a.due_date && !b.due_date) return 0;
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return a.due_date.localeCompare(b.due_date);
      });
    }
    if (sortBy === 'priority') {
      return copy.sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]);
    }
    return copy.sort((a, b) => b.id - a.id);
  }, [tasks, sortBy]);

  const totalPages = Math.max(1, Math.ceil(sortedTasks.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages - 1);
  const pageTasks = sortedTasks.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE);

  async function addTask(input: { title: string; description?: string; priority: Priority; due_date?: string | null }) {
    const res = await createTask(input);
    if (res.ok) await fetchTasks();
    return res;
  }

  async function editTask(id: number, fields: Partial<Task>) {
    const res = await updateTask(id, fields);
    if (res.ok) await fetchTasks();
    return res;
  }

  async function removeTask(id: number) {
    const res = await deleteTask(id);
    if (res.ok) await fetchTasks();
    return res;
  }

  async function markAllDone() {
    const pending = sortedTasks.filter((t) => t.status !== 'completed');
    const results = await Promise.all(pending.map((t) => updateTask(t.id, { status: 'completed' })));
    await fetchTasks();
    return results.filter((r) => !r.ok).length;
  }

  async function deleteCompleted() {
    const completed = sortedTasks.filter((t) => t.status === 'completed');
    const results = await Promise.all(completed.map((t) => deleteTask(t.id)));
    await fetchTasks();
    return results.filter((r) => !r.ok).length;
  }

  return {
    tasks: pageTasks,
    allFilteredTasks: sortedTasks,
    loading,
    error,
    keyword,
    setKeyword,
    statusFilter,
    setStatusFilter,
    priorityFilter,
    setPriorityFilter,
    sortBy,
    setSortBy,
    page: currentPage,
    setPage,
    totalPages,
    addTask,
    editTask,
    removeTask,
    markAllDone,
    deleteCompleted,
    refetch: fetchTasks,
  };
}

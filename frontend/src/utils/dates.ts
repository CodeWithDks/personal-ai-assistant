/**
 * Returns 'overdue', 'today', or null for a pending task's due date.
 * Completed tasks and tasks with no due date never get a status.
 */
export function taskDueStatus(task: { status: string; due_date?: string | null }): 'overdue' | 'today' | null {
  if (task.status === 'completed' || !task.due_date) return null;

  const due = new Date(task.due_date);
  if (Number.isNaN(due.getTime())) return null;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const dueDay = new Date(due.getFullYear(), due.getMonth(), due.getDate());

  if (dueDay < today) return 'overdue';
  if (dueDay.getTime() === today.getTime()) return 'today';
  return null;
}

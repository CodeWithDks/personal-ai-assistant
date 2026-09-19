import { FormEvent, useState } from 'react';
import type { ApiResult, Priority, Task } from '../../types';

export function TaskForm({
  onCreate,
}: {
  onCreate: (input: { title: string; description?: string; priority: Priority; due_date?: string | null }) => Promise<ApiResult<Task>>;
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Priority>('medium');
  const [dueDate, setDueDate] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError("Title can't be empty.");
      return;
    }
    setSubmitting(true);
    const res = await onCreate({
      title: title.trim(),
      description: description.trim() || undefined,
      priority,
      due_date: dueDate ? new Date(dueDate).toISOString() : null,
    });
    setSubmitting(false);
    if (res.ok) {
      setTitle('');
      setDescription('');
      setPriority('medium');
      setDueDate('');
      setError(null);
      setOpen(false);
    } else {
      setError(res.error);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mb-4 w-full rounded-xl border border-dashed border-border py-3 text-sm text-muted transition hover:border-signal hover:text-signal"
      >
        ➕ Add a new task
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mb-4 flex flex-col gap-3 rounded-xl border border-border bg-surface p-4">
      <div className="flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title *"
          className="flex-1 rounded-lg border border-border px-3 py-2 text-sm"
        />
        <select value={priority} onChange={(e) => setPriority(e.target.value as Priority)} className="rounded-lg border border-border px-2 text-sm">
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
      </div>
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Description (optional)"
        rows={2}
        className="rounded-lg border border-border px-3 py-2 text-sm"
      />
      <input
        type="datetime-local"
        value={dueDate}
        onChange={(e) => setDueDate(e.target.value)}
        className="rounded-lg border border-border px-3 py-2 text-sm text-muted"
      />
      {error && <p className="rounded-md bg-danger-soft px-3 py-2 text-xs text-danger">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-signal px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? 'Creating…' : 'Create task'}
        </button>
        <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-border px-4 py-2 text-sm text-muted">
          Cancel
        </button>
      </div>
    </form>
  );
}

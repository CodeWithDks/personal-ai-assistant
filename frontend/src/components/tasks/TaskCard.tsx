import { useState } from 'react';
import type { ApiResult, Priority, Task } from '../../types';
import { Badge } from '../shared/Badge';
import { ConfirmButton } from '../shared/ConfirmButton';
import { taskDueStatus } from '../../utils/dates';

const PRIORITY_EMOJI: Record<Priority, string> = { high: '🔴', medium: '🟡', low: '🟢' };

export function TaskCard({
  task,
  onToggleDone,
  onEdit,
  onDelete,
}: {
  task: Task;
  onToggleDone: () => void;
  onEdit: (fields: Partial<Task>) => Promise<ApiResult<Task | null>>;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [priority, setPriority] = useState<Priority>(task.priority);
  const [saving, setSaving] = useState(false);

  const done = task.status === 'completed';
  const dueStatus = taskDueStatus(task);

  async function saveEdit() {
    setSaving(true);
    await onEdit({
      title: title !== task.title ? title : undefined,
      priority: priority !== task.priority ? priority : undefined,
    });
    setSaving(false);
    setEditing(false);
  }

  return (
    <div className="rounded-xl border border-border bg-surface p-4 transition hover:shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {editing ? (
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border border-border px-2 py-1 text-sm"
            />
          ) : (
            <p className={`font-medium text-ink ${done ? 'text-muted line-through' : ''}`}>
              <span className="mr-1">{PRIORITY_EMOJI[task.priority]}</span>
              {task.title}
            </p>
          )}

          {task.description && <p className="mt-1 text-sm text-muted">{task.description}</p>}

          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {dueStatus === 'overdue' && <Badge variant="danger">⏰ overdue</Badge>}
            {dueStatus === 'today' && <Badge variant="ember">📅 due today</Badge>}
            <Badge variant={done ? 'success' : 'signal'}>{done ? '✓ completed' : 'pending'}</Badge>
            {task.due_date && <span className="font-mono text-xs text-muted">due {task.due_date.slice(0, 10)}</span>}
          </div>
        </div>

        <div className="flex flex-shrink-0 items-center gap-1">
          {editing ? (
            <>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as Priority)}
                className="rounded-md border border-border px-1 py-1 text-xs"
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
              <button
                onClick={saveEdit}
                disabled={saving}
                className="rounded-md bg-signal px-2 py-1 text-xs text-white disabled:opacity-50"
              >
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button onClick={() => setEditing(false)} className="rounded-md border border-border px-2 py-1 text-xs">
                Cancel
              </button>
            </>
          ) : (
            <>
              {!done && (
                <button onClick={onToggleDone} className="rounded-md px-2 py-1 text-xs text-signal hover:bg-signal-soft">
                  ✅ Done
                </button>
              )}
              <button onClick={() => setEditing(true)} className="rounded-md px-2 py-1 text-xs text-muted hover:bg-subtle">
                ✏️
              </button>
              <ConfirmButton onConfirm={onDelete} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

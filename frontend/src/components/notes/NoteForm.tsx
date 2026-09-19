import { FormEvent, useState } from 'react';
import type { ApiResult, Note } from '../../types';

export function NoteForm({ onCreate }: { onCreate: (input: { title?: string; content: string }) => Promise<ApiResult<Note>> }) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!content.trim()) {
      setError("Content can't be empty.");
      return;
    }
    setSubmitting(true);
    const res = await onCreate({ title: title.trim() || undefined, content: content.trim() });
    setSubmitting(false);
    if (res.ok) {
      setTitle('');
      setContent('');
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
        ➕ Add a new note
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mb-4 flex flex-col gap-3 rounded-xl border border-border bg-surface p-4">
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Title (optional)"
        className="rounded-lg border border-border px-3 py-2 text-sm"
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Content *"
        rows={4}
        className="rounded-lg border border-border px-3 py-2 text-sm"
      />
      {error && <p className="rounded-md bg-danger-soft px-3 py-2 text-xs text-danger">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-signal px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? 'Creating…' : 'Create note'}
        </button>
        <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-border px-4 py-2 text-sm text-muted">
          Cancel
        </button>
      </div>
    </form>
  );
}

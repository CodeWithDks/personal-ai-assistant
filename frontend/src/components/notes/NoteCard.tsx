import { useState } from 'react';
import type { ApiResult, Note } from '../../types';
import { ConfirmButton } from '../shared/ConfirmButton';

export function NoteCard({
  note,
  onEdit,
  onDelete,
}: {
  note: Note;
  onEdit: (fields: Partial<Pick<Note, 'title' | 'content'>>) => Promise<ApiResult<Note | null>>;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(note.title ?? '');
  const [content, setContent] = useState(note.content);
  const [saving, setSaving] = useState(false);

  async function saveEdit() {
    setSaving(true);
    await onEdit({
      title: title !== (note.title ?? '') ? title : undefined,
      content: content !== note.content ? content : undefined,
    });
    setSaving(false);
    setEditing(false);
  }

  return (
    <div className="rounded-xl border border-border bg-surface p-4 transition hover:shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {editing ? (
            <div className="flex flex-col gap-2">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Title (optional)"
                className="w-full rounded-md border border-border px-2 py-1 text-sm font-medium"
              />
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-border px-2 py-1 text-sm"
              />
            </div>
          ) : (
            <>
              {note.title && <p className="font-medium text-ink">{note.title}</p>}
              <p className="mt-1 whitespace-pre-wrap text-sm text-ink">{note.content}</p>
              <p className="mt-2 font-mono text-xs text-muted">created {note.created_at.slice(0, 10)}</p>
            </>
          )}
        </div>

        <div className="flex flex-shrink-0 items-center gap-1">
          {editing ? (
            <>
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

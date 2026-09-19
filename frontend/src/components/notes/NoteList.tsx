import { useNotes } from '../../hooks/useNotes';
import { EmptyState } from '../shared/EmptyState';
import { Pagination } from '../shared/Pagination';
import { Spinner } from '../shared/Spinner';
import { NoteCard } from './NoteCard';
import { NoteForm } from './NoteForm';

export function NoteList() {
  const n = useNotes();

  return (
    <div>
      <NoteForm onCreate={n.addNote} />

      <div className="mb-3 flex gap-2">
        <input
          value={n.keyword}
          onChange={(e) => n.setKeyword(e.target.value)}
          placeholder="Search keyword"
          className="flex-1 rounded-lg border border-border px-3 py-1.5 text-sm"
        />
        <button onClick={n.refetch} className="rounded-lg border border-border px-3 py-1.5 text-sm text-muted hover:bg-subtle-hover">
          🔄
        </button>
      </div>

      {n.error && <p className="mb-3 rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{n.error}</p>}

      {n.loading ? (
        <Spinner />
      ) : n.allNotes.length === 0 ? (
        <EmptyState icon="🗒️" title="No notes found" subtitle={n.keyword ? 'Try a different keyword.' : 'Jot something down above.'} />
      ) : (
        <>
          <div className="flex flex-col gap-2">
            {n.notes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                onEdit={(fields) => n.editNote(note.id, fields)}
                onDelete={() => n.removeNote(note.id)}
              />
            ))}
          </div>
          <Pagination page={n.page} totalPages={n.totalPages} onChange={n.setPage} />
        </>
      )}
    </div>
  );
}

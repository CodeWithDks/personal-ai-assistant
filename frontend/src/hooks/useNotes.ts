import { useCallback, useEffect, useMemo, useState } from 'react';
import { createNote, deleteNote, getNotes, searchNotes, updateNote } from '../api/notes';
import type { Note } from '../types';

const PAGE_SIZE = 10;

export function useNotes() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(0);

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = keyword ? await searchNotes({ keyword }) : await getNotes();
    setLoading(false);
    if (res.ok) setNotes(res.data);
    else setError(res.error);
  }, [keyword]);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  const totalPages = Math.max(1, Math.ceil(notes.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages - 1);
  const pageNotes = useMemo(
    () => notes.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE),
    [notes, currentPage]
  );

  async function addNote(input: { title?: string; content: string }) {
    const res = await createNote(input);
    if (res.ok) await fetchNotes();
    return res;
  }

  async function editNote(id: number, fields: Partial<Pick<Note, 'title' | 'content'>>) {
    const res = await updateNote(id, fields);
    if (res.ok) await fetchNotes();
    return res;
  }

  async function removeNote(id: number) {
    const res = await deleteNote(id);
    if (res.ok) await fetchNotes();
    return res;
  }

  return {
    notes: pageNotes,
    allNotes: notes,
    loading,
    error,
    keyword,
    setKeyword,
    page: currentPage,
    setPage,
    totalPages,
    addNote,
    editNote,
    removeNote,
    refetch: fetchNotes,
  };
}

export function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;
  return (
    <div className="mt-4 flex items-center justify-center gap-4 font-mono text-sm text-muted">
      <button disabled={page === 0} onClick={() => onChange(page - 1)} className="disabled:opacity-30">
        ← Prev
      </button>
      <span>
        Page {page + 1} of {totalPages}
      </span>
      <button disabled={page >= totalPages - 1} onClick={() => onChange(page + 1)} className="disabled:opacity-30">
        Next →
      </button>
    </div>
  );
}

export function BulkActions({
  pendingCount,
  completedCount,
  onMarkAllDone,
  onDeleteCompleted,
}: {
  pendingCount: number;
  completedCount: number;
  onMarkAllDone: () => void;
  onDeleteCompleted: () => void;
}) {
  return (
    <div className="mb-3 flex gap-2">
      <button
        onClick={onMarkAllDone}
        disabled={!pendingCount}
        className="rounded-lg border border-border px-3 py-1.5 text-xs text-ink hover:bg-signal-soft disabled:opacity-40"
      >
        ✅ Mark all done ({pendingCount})
      </button>
      <button
        onClick={onDeleteCompleted}
        disabled={!completedCount}
        className="rounded-lg border border-border px-3 py-1.5 text-xs text-ink hover:bg-danger-soft disabled:opacity-40"
      >
        🗑️ Delete completed ({completedCount})
      </button>
    </div>
  );
}

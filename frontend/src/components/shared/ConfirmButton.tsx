import { useState } from 'react';

/**
 * Two-click delete: first click arms a confirm/cancel pair for this
 * specific item; a second click actually deletes. Clicking anything
 * else on the page never triggers a delete because the "armed" state
 * lives inside this one component instance, not shared page state.
 */
export function ConfirmButton({ onConfirm }: { onConfirm: () => void }) {
  const [confirming, setConfirming] = useState(false);

  if (confirming) {
    return (
      <div className="flex gap-1">
        <button
          onClick={() => {
            onConfirm();
            setConfirming(false);
          }}
          className="rounded-md bg-danger px-2 py-1 text-xs font-mono text-white hover:bg-danger/90"
        >
          Confirm
        </button>
        <button
          onClick={() => setConfirming(false)}
          className="rounded-md border border-border px-2 py-1 text-xs text-muted hover:bg-subtle-hover"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setConfirming(true)}
      aria-label="Delete"
      className="rounded-md px-2 py-1 text-muted hover:bg-danger-soft hover:text-danger"
    >
      🗑️
    </button>
  );
}

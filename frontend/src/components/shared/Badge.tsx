import type { ReactNode } from 'react';

type BadgeVariant = 'signal' | 'ember' | 'danger' | 'success' | 'muted';

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  signal: 'bg-signal-soft text-signal',
  ember: 'bg-ember-soft text-ember',
  danger: 'bg-danger-soft text-danger',
  success: 'bg-success-soft text-success',
  muted: 'bg-subtle text-muted',
};

// Badges render in monospace — the "system voice" of the app, used
// consistently for status labels, timestamps, and chat replies.
export function Badge({ children, variant = 'muted' }: { children: ReactNode; variant?: BadgeVariant }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 font-mono text-xs font-medium ${VARIANT_CLASSES[variant]}`}
    >
      {children}
    </span>
  );
}

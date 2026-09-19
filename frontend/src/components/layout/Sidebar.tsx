import { useAuth } from '../../context/AuthContext';
import { ThemeToggle } from '../shared/ThemeToggle';

export type Mode = 'chat' | 'simple';

export function Sidebar({ mode, onModeChange }: { mode: Mode; onModeChange: (mode: Mode) => void }) {
  const { userEmail, signOut } = useAuth();

  return (
    <aside className="flex w-56 flex-shrink-0 flex-col gap-4 border-r border-border pr-4">
      <div>
        <p className="text-xs font-mono text-muted">Logged in as</p>
        <p className="truncate text-sm text-ink">{userEmail}</p>
      </div>
      <nav className="flex flex-col gap-1">
        <button
          onClick={() => onModeChange('chat')}
          className={`rounded-lg px-3 py-2 text-left text-sm ${mode === 'chat' ? 'bg-signal-soft text-signal' : 'text-ink hover:bg-subtle'}`}
        >
          💬 Agent (Chat)
        </button>
        <button
          onClick={() => onModeChange('simple')}
          className={`rounded-lg px-3 py-2 text-left text-sm ${mode === 'simple' ? 'bg-signal-soft text-signal' : 'text-ink hover:bg-subtle'}`}
        >
          🗂️ Simple (Direct)
        </button>
      </nav>
      <div className="mt-auto flex flex-col gap-2">
        <ThemeToggle />
        <button
          onClick={signOut}
          className="rounded-lg border border-border py-2 text-sm text-muted hover:bg-subtle-hover"
        >
          🚪 Log out
        </button>
      </div>
    </aside>
  );
}

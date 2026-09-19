import { useTheme } from '../../context/ThemeContext';

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className={`flex items-center gap-2 rounded-lg border border-border text-sm text-ink transition hover:bg-subtle ${
        compact ? 'p-2' : 'px-3 py-2'
      }`}
    >
      <span>{isDark ? '🌙' : '☀️'}</span>
      {!compact && <span>{isDark ? 'Dark' : 'Light'}</span>}
    </button>
  );
}

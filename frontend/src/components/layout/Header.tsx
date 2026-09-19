export function Header() {
  return (
    <header className="mb-6 flex items-center gap-3 rounded-2xl bg-signal px-5 py-4 text-white">
      <span className="text-2xl">🧠</span>
      <div>
        <h1 className="font-display text-lg leading-tight">Personal AI Assistant</h1>
        <p className="font-mono text-xs text-white/70">chat naturally, or manage tasks &amp; notes directly</p>
      </div>
    </header>
  );
}

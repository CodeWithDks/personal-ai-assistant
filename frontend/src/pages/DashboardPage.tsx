import { useState } from 'react';
import { ChatWindow } from '../components/chat/ChatWindow';
import { Header } from '../components/layout/Header';
import { Sidebar, type Mode } from '../components/layout/Sidebar';
import { NoteList } from '../components/notes/NoteList';
import { TaskList } from '../components/tasks/TaskList';

type SimpleTab = 'tasks' | 'notes';

export function DashboardPage() {
  const [mode, setMode] = useState<Mode>('chat');
  const [tab, setTab] = useState<SimpleTab>('tasks');

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <Header />
      <div className="flex gap-6">
        <Sidebar mode={mode} onModeChange={setMode} />
        <main className="min-w-0 flex-1">
          {mode === 'chat' ? (
            <ChatWindow />
          ) : (
            <>
              <p className="mb-4 text-sm text-muted">Direct task/note management — no LLM involved.</p>
              <div className="mb-4 flex w-fit gap-1 rounded-lg bg-subtle p-1 font-mono text-sm">
                <button
                  onClick={() => setTab('tasks')}
                  className={`rounded-md px-4 py-1.5 transition ${tab === 'tasks' ? 'bg-surface text-ink shadow-sm' : 'text-muted'}`}
                >
                  📋 Tasks
                </button>
                <button
                  onClick={() => setTab('notes')}
                  className={`rounded-md px-4 py-1.5 transition ${tab === 'notes' ? 'bg-surface text-ink shadow-sm' : 'text-muted'}`}
                >
                  🗒️ Notes
                </button>
              </div>
              {tab === 'tasks' ? <TaskList /> : <NoteList />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

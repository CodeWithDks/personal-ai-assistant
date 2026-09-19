import { useState } from 'react';
import { ThemeToggle } from '../shared/ThemeToggle';
import { LoginForm } from './LoginForm';
import { RegisterForm } from './RegisterForm';

export function AuthScreen() {
  const [tab, setTab] = useState<'login' | 'register'>('login');

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="absolute right-4 top-4">
        <ThemeToggle compact />
      </div>
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="text-3xl">🧠</div>
          <h1 className="mt-2 font-display text-2xl text-ink">Personal AI Assistant</h1>
          <p className="mt-1 text-sm text-muted">Sign in or create an account to continue.</p>
        </div>
        <div className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
          <div className="mb-6 flex gap-1 rounded-lg bg-subtle p-1 font-mono text-sm">
            <button
              onClick={() => setTab('login')}
              className={`flex-1 rounded-md py-1.5 transition ${tab === 'login' ? 'bg-surface text-ink shadow-sm' : 'text-muted'}`}
            >
              Login
            </button>
            <button
              onClick={() => setTab('register')}
              className={`flex-1 rounded-md py-1.5 transition ${tab === 'register' ? 'bg-surface text-ink shadow-sm' : 'text-muted'}`}
            >
              Register
            </button>
          </div>
          {tab === 'login' ? <LoginForm /> : <RegisterForm onRegistered={() => setTab('login')} />}
        </div>
      </div>
    </div>
  );
}

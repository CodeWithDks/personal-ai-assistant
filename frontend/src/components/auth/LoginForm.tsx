import { FormEvent, useState } from 'react';
import { login as loginRequest } from '../../api/auth';
import { useAuth } from '../../context/AuthContext';

export function LoginForm() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('Enter both email and password.');
      return;
    }
    setLoading(true);
    const res = await loginRequest(email, password);
    setLoading(false);
    if (res.ok) {
      signIn(res.data.access_token, email);
    } else {
      setError(res.error);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div>
        <label className="mb-1 block text-xs font-mono text-muted">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="w-full rounded-lg border border-border px-3 py-2 text-sm focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs font-mono text-muted">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-border px-3 py-2 text-sm focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal"
        />
      </div>
      {error && <p className="rounded-md bg-danger-soft px-3 py-2 text-xs text-danger">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="mt-1 rounded-lg bg-signal py-2 text-sm font-medium text-white hover:bg-signal/90 disabled:opacity-50"
      >
        {loading ? 'Logging in…' : 'Log in'}
      </button>
    </form>
  );
}

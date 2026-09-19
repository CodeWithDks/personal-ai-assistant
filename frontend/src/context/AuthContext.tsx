import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { AUTH_EXPIRED_EVENT, TOKEN_KEY } from '../api/client';

const EMAIL_KEY = 'pai_email';

interface AuthContextValue {
  userEmail: string | null;
  isAuthenticated: boolean;
  signIn: (token: string, email: string) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [userEmail, setUserEmail] = useState<string | null>(() => localStorage.getItem(EMAIL_KEY));

  function signIn(newToken: string, email: string) {
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(EMAIL_KEY, email);
    setToken(newToken);
    setUserEmail(email);
  }

  function signOut() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
    setToken(null);
    setUserEmail(null);
  }

  // A 401 from any API call dispatches this event (see api/client.ts).
  // Listening here means an expired session logs the user out and
  // shows the login screen, wherever in the app it happened.
  useEffect(() => {
    window.addEventListener(AUTH_EXPIRED_EVENT, signOut);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, signOut);
  }, []);

  return (
    <AuthContext.Provider value={{ userEmail, isAuthenticated: !!token, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}

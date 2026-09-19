export type Priority = 'low' | 'medium' | 'high';
export type TaskStatus = 'pending' | 'completed';

export interface Task {
  id: number;
  title: string;
  description?: string | null;
  priority: Priority;
  status: TaskStatus;
  due_date?: string | null;
}

export interface Note {
  id: number;
  title?: string | null;
  content: string;
  created_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  isVoice?: boolean;      // true if this user message came from a voice recording
  audioUrl?: string;      // playable audio for an assistant voice reply (data: URL)
}

export interface VoiceChatResponse {
  transcript: string;
  reply: string;
  audio_base64: string;
  audio_format: string;
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
}

// Every api/* function resolves to one of these — mirrors the
// (ok, data_or_error) tuple pattern from the original Streamlit app,
// so callers never have to guess the shape of a failed response.
export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

import { FormEvent, useEffect, useRef, useState } from 'react';
import { sendChatMessage, sendVoiceMessage } from '../../api/chat';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import type { ChatMessage } from '../../types';
import { ChatMessageBubble } from './ChatMessageBubble';

export function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const recorder = useAudioRecorder();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending, recorder.isRecording]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    setMessages((m) => [...m, { role: 'user', content: text }]);
    setInput('');
    setSending(true);
    setError(null);

    const res = await sendChatMessage(text);
    setSending(false);

    if (res.ok) {
      setMessages((m) => [...m, { role: 'assistant', content: res.data.reply }]);
    } else {
      setError(res.error);
    }
  }

  async function handleMicClick() {
    setError(null);
    if (recorder.isRecording) {
      const blob = await recorder.stop();
      if (!blob) return;

      setSending(true);
      const res = await sendVoiceMessage(blob);
      setSending(false);

      if (res.ok) {
        const { transcript, reply, audio_base64, audio_format } = res.data;
        setMessages((m) => [
          ...m,
          { role: 'user', content: transcript, isVoice: true },
          {
            role: 'assistant',
            content: reply,
            audioUrl: `data:audio/${audio_format};base64,${audio_base64}`,
          },
        ]);
      } else {
        setError(res.error);
      }
    } else {
      const startError = await recorder.start();
      if (startError) setError(startError);
    }
  }

  return (
    <div className="flex h-[70vh] flex-col rounded-2xl border border-border bg-surface">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-muted">
            Talk to it naturally — "remind me to call the plumber", "what's on my plate today", etc.
          </p>
        )}
        {messages.map((m, i) => (
          <ChatMessageBubble key={i} message={m} />
        ))}
        {sending && <p className="font-mono text-xs text-muted">assistant is thinking…</p>}
        {recorder.isRecording && (
          <p className="flex items-center gap-2 font-mono text-xs text-danger">
            <span className="h-2 w-2 animate-pulse rounded-full bg-danger" />
            recording… tap the mic again to send
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="mx-4 mb-2 rounded-md bg-danger-soft px-3 py-2 text-xs text-danger">{error}</p>}

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border p-3">
        <button
          type="button"
          onClick={handleMicClick}
          disabled={sending}
          aria-label={recorder.isRecording ? 'Stop recording and send' : 'Record a voice message'}
          className={`rounded-lg px-3 py-2 text-sm transition disabled:opacity-50 ${
            recorder.isRecording
              ? 'animate-pulse bg-danger text-white'
              : 'border border-border text-muted hover:bg-signal-soft hover:text-signal'
          }`}
        >
          {recorder.isRecording ? '⏹' : '🎤'}
        </button>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={recorder.isRecording ? 'Recording…' : 'Type a message…'}
          disabled={recorder.isRecording}
          className="flex-1 rounded-lg border border-border px-3 py-2 text-sm disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={sending || recorder.isRecording}
          className="rounded-lg bg-signal px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Send
        </button>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={() => setMessages([])}
            className="rounded-lg border border-border px-3 py-2 text-sm text-muted"
            aria-label="Clear conversation"
          >
            🧹
          </button>
        )}
      </form>
    </div>
  );
}

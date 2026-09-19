import { useRef, useState } from 'react';
import type { ChatMessage } from '../../types';

// Signature design choice: user messages render in the body sans
// font (their voice); assistant replies render in monospace (the
// system's voice) — a visual cue for who's "talking" that doesn't
// rely on color or position alone.
export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
    } else {
      audio.play();
    }
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
          isUser ? 'bg-signal text-white' : 'bg-subtle font-mono text-ink'
        }`}
      >
        {isUser && message.isVoice && <span className="mr-1.5 opacity-80">🎤</span>}
        {message.content}

        {message.audioUrl && (
          <div className="mt-2 flex items-center gap-2">
            <button
              type="button"
              onClick={togglePlay}
              className={`rounded-full px-2 py-1 text-xs ${
                isUser ? 'bg-white/20 hover:bg-white/30' : 'bg-surface text-signal hover:bg-signal-soft'
              }`}
              aria-label={playing ? 'Pause reply audio' : 'Play reply audio'}
            >
              {playing ? '⏸' : '▶'} audio
            </button>
            <audio
              ref={audioRef}
              src={message.audioUrl}
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onEnded={() => setPlaying(false)}
              className="hidden"
            />
          </div>
        )}
      </div>
    </div>
  );
}

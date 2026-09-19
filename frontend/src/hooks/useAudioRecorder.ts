import { useCallback, useRef, useState } from 'react';

/**
 * Wraps the browser's MediaRecorder API behind a small start/stop
 * interface. Keeps microphone/stream lifecycle details out of
 * ChatWindow — it just calls start() and awaits stop().
 */
export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // Returns an error message on failure, or null on success. Returning
  // it directly (rather than only setting state) lets the caller act
  // on the outcome immediately, without reading a stale closure value
  // from `error` on the same render pass.
  const start = useCallback(async (): Promise<string | null> => {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      const msg = 'Voice recording is not supported in this browser.';
      setError(msg);
      return msg;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      return null;
    } catch {
      const msg = 'Microphone access was denied or is unavailable.';
      setError(msg);
      return msg;
    }
  }, []);

  const stop = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === 'inactive') {
        setIsRecording(false);
        resolve(null);
        return;
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
        mediaRecorderRef.current = null;
        setIsRecording(false);
        resolve(blob);
      };
      recorder.stop();
    });
  }, []);

  return { isRecording, error, start, stop };
}

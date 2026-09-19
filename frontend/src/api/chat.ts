import { apiClient, getErrorMessage } from './client';
import type { ApiResult, VoiceChatResponse } from '../types';

export async function sendChatMessage(message: string): Promise<ApiResult<{ reply: string }>> {
  try {
    const { data } = await apiClient.post<{ reply: string }>('/chat/', { message });
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

export async function sendVoiceMessage(audioBlob: Blob): Promise<ApiResult<VoiceChatResponse>> {
  try {
    // Backend expects a multipart file field named "audio" (FastAPI's
    // `audio: UploadFile = File(...)`). Letting the browser set its own
    // Content-Type (with the multipart boundary) is required here —
    // setting it manually breaks the boundary.
    const form = new FormData();
    form.append('audio', audioBlob, 'recording.webm');
    const { data } = await apiClient.post<VoiceChatResponse>('/chat/voice', form);
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: getErrorMessage(e) };
  }
}

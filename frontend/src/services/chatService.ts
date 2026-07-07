// src/services/chatService.ts

import api from './api';
import type { BackendResponse } from '../types';

/**
 * Send a natural-language query to the backend AI pipeline.
 *
 * Endpoint: POST /api/v1/chat/query
 * Payload : { "message": "<user input>" }
 *
 * The backend classifies intent and returns a structured response whose shape
 * varies by intent (PREDICT_CRIME includes a `prediction` object, SEARCH_CASES
 * includes `results`, AGGREGATE_COUNT includes `count`, etc.).
 */
export const sendChatMessage = async (message: string): Promise<BackendResponse> => {
  const response = await api.post<BackendResponse>('/chat/query', { message });
  return response.data;
};

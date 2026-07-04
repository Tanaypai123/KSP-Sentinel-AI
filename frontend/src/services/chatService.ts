// src/services/chatService.ts

import api from './api';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  [key: string]: any;
}

/** Send a message to the AI chat endpoint */
export const sendChatMessage = async (message: string): Promise<ChatMessage> => {
  const response = await api.post('/chat', { message });
  return response.data;
};

/** Retrieve chat history (if available) */
export const getChatHistory = async (page: number = 1, pageSize: number = 20): Promise<ChatMessage[]> => {
  const response = await api.get('/chat/history', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

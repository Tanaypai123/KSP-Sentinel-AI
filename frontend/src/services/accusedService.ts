// src/services/accusedService.ts

import api from './api';

export interface Accused {
  id: number;
  // Add other fields as defined by backend schema
  [key: string]: any;
}

/** Retrieve a paginated list of accused */
export const getAccused = async (page: number = 1, pageSize: number = 20): Promise<Accused[]> => {
  const response = await api.get('/accused', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

/** Retrieve an accused by ID */
export const getAccusedById = async (id: number): Promise<Accused> => {
  const response = await api.get(`/accused/${id}`);
  return response.data;
};

/** Search accused */
export const searchAccused = async (query: string, page: number = 1, pageSize: number = 20): Promise<Accused[]> => {
  const response = await api.get('/accused/search', {
    params: { q: query, page, page_size: pageSize },
  });
  return response.data;
};

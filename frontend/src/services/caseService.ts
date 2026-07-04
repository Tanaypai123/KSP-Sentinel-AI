// src/services/caseService.ts

import api from './api';

export interface Case {
  id: number;
  // Add other fields as defined by backend schema
  [key: string]: any;
}

/** Retrieve a paginated list of cases */
export const getCases = async (page: number = 1, pageSize: number = 20): Promise<Case[]> => {
  const response = await api.get('/cases', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

/** Retrieve a single case by ID */
export const getCaseById = async (id: number): Promise<Case> => {
  const response = await api.get(`/cases/${id}`);
  return response.data;
};

/** Search cases */
export const searchCases = async (query: string, page: number = 1, pageSize: number = 20): Promise<Case[]> => {
  const response = await api.get('/cases/search', {
    params: { q: query, page, page_size: pageSize },
  });
  return response.data;
};

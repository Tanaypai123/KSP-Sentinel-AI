// src/services/reportService.ts

import api from './api';

export interface Report {
  // Define fields returned by the dashboard report endpoint
  [key: string]: any;
}

/** Fetch dashboard report data */
export const getDashboardReport = async (): Promise<Report> => {
  const response = await api.get('/reports/dashboard');
  return response.data;
};

/** Fetch all reports (optional) */
export const getAllReports = async (page: number = 1, pageSize: number = 20): Promise<Report[]> => {
  const response = await api.get('/reports', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

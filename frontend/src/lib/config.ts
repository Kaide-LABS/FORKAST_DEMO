// API configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// API endpoints
export const API_ENDPOINTS = {
  competitors: `${API_BASE_URL}/api/v1/competitors`,
  dashboard: `${API_BASE_URL}/api/v1/dashboard`,
  alerts: `${API_BASE_URL}/api/v1/alerts`,
  scraping: `${API_BASE_URL}/api/v1/scraping`,
} as const;

// API configuration
// Use production URL as fallback for client-side code
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://forkast-api-511464604796.us-central1.run.app';

// API endpoints
export const API_ENDPOINTS = {
  competitors: `${API_BASE_URL}/api/v1/competitors`,
  dashboard: `${API_BASE_URL}/api/v1/dashboard`,
  alerts: `${API_BASE_URL}/api/v1/alerts`,
  scraping: `${API_BASE_URL}/api/v1/scraping`,
} as const;

// API configuration
// In development, use local backend; in production, use deployed backend

const IS_DEV = process.env.NODE_ENV === 'development';

// For server-side (SSR, server components) - direct backend URL
export const SERVER_API_URL = IS_DEV
  ? 'http://127.0.0.1:8000'
  : 'https://forkast-api-84498540486.us-central1.run.app';

// For client-side (browser) - use proxy to avoid CORS issues
export const CLIENT_API_URL = '/api/proxy';

// Default export for client components
export const API_BASE_URL = CLIENT_API_URL;

// API endpoints (for client components)
// Note: Tenant ID is automatically added by the API proxy using Clerk session
export const API_ENDPOINTS = {
  competitors: `${CLIENT_API_URL}/api/v1/competitors`,
  dashboard: `${CLIENT_API_URL}/api/v1/dashboard`,
  alerts: `${CLIENT_API_URL}/api/v1/alerts`,
  scraping: `${CLIENT_API_URL}/api/v1/scraping`,
  operator: `${CLIENT_API_URL}/api/v1/operator`,
  categories: `${CLIENT_API_URL}/api/v1/categories`,
} as const;

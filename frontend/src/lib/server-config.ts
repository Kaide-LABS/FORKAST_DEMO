import { auth } from '@/auth';

// Server-side API URL
const IS_DEV = process.env.NODE_ENV === 'development';

export const SERVER_API_URL = IS_DEV
  ? 'http://127.0.0.1:8000'
  : 'https://forkast-api-84498540486.us-central1.run.app';

// Get tenant ID from NextAuth session (for server-side use)
export async function getServerTenantId(): Promise<string> {
  const session = await auth();
  return session?.user?.id || 'default';
}

// Get headers with tenant ID for server-side fetch calls
export async function getServerApiHeaders(): Promise<Record<string, string>> {
  const tenantId = await getServerTenantId();
  return {
    'Content-Type': 'application/json',
    'X-Tenant-ID': tenantId,
  };
}

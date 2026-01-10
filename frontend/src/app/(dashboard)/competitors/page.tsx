// Competitors Page - Server Component

import CompetitorsHeader from '@/components/CompetitorsHeader';
import AddCompetitorButton from '@/components/AddCompetitorButton';
import CompetitorCard from '@/components/CompetitorCard';
import { SERVER_API_URL, getServerApiHeaders } from '@/lib/server-config';

interface Competitor {
  id: string;
  name: string;
  location: string;
  concept_type: string;
  doordash_url: string | null;
  ubereats_url: string | null;
  scraping_enabled: boolean;
  last_scraped_at: string | null;
  created_at: string;
  updated_at: string;
  items_count?: number;
}

async function fetchCompetitors(): Promise<Competitor[] | null> {
  try {
    // Use the endpoint that includes item counts
    const res = await fetch(`${SERVER_API_URL}/api/v1/competitors/with-stats/all`, {
      cache: 'no-store',
      headers: await getServerApiHeaders(),
    });

    if (!res.ok) {
      throw new Error('Failed to fetch competitors');
    }

    return res.json();
  } catch (error) {
    console.error('Competitors fetch error:', error);
    return null;
  }
}

export default async function CompetitorsPage() {
  const competitors = await fetchCompetitors();

  if (!competitors) {
    return (
      <div className="space-y-6">
        <CompetitorsHeader />
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800">Backend Unavailable</h2>
          <p className="text-red-600 mt-2">
            Unable to connect to the backend server. Please ensure it&apos;s running.
          </p>
        </div>
      </div>
    );
  }

  // Calculate total items tracked
  const totalItems = competitors.reduce((sum, c) => sum + (c.items_count || 0), 0);

  return (
    <div className="space-y-8">
      {/* Page Header with Add Competitor Button */}
      <CompetitorsHeader />

      {/* Competitors Grid */}
      {competitors.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {competitors.map((competitor) => (
            <CompetitorCard key={competitor.id} competitor={competitor} />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 21v-7.5a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 .75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349M3.75 21V9.349m0 0a3.001 3.001 0 0 0 3.75-.615A2.993 2.993 0 0 0 9.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 0 0 2.25 1.016c.896 0 1.7-.393 2.25-1.015a3.001 3.001 0 0 0 3.75.614m-16.5 0a3.004 3.004 0 0 1-.621-4.72l1.189-1.19A1.5 1.5 0 0 1 5.378 3h13.243a1.5 1.5 0 0 1 1.06.44l1.19 1.189a3 3 0 0 1-.621 4.72M6.75 18h3.75a.75.75 0 0 0 .75-.75V13.5a.75.75 0 0 0-.75-.75H6.75a.75.75 0 0 0-.75.75v3.75c0 .414.336.75.75.75Z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900">No competitors yet</h3>
          <p className="text-gray-500 mt-2 max-w-sm mx-auto">
            Start tracking your competitors by adding them to your dashboard.
          </p>
          <div className="mt-6">
            <AddCompetitorButton />
          </div>
        </div>
      )}

      {/* Summary */}
      {competitors.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-gray-500">Total Competitors: </span>
              <span className="font-medium text-gray-900">{competitors.length}</span>
            </div>
            <div>
              <span className="text-gray-500">Active: </span>
              <span className="font-medium text-green-600">
                {competitors.filter((c) => c.scraping_enabled).length}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Total Items Tracked: </span>
              <span className="font-medium text-indigo-600">{totalItems}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

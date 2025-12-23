// Alerts Page - Server Component

import Link from 'next/link';
import AlertsList from '@/components/AlertsList';

interface Alert {
  id: string;
  menu_item_id: string;
  alert_type: string;
  old_value: string | null;
  new_value: string | null;
  change_percentage: string | number | null;
  is_acknowledged: boolean;
  created_at: string;
  item_name: string | null;
  competitor_name: string | null;
}

interface AlertsResponse {
  alerts: Alert[];
  unacknowledged_count: number;
  total_count: number;
}

async function fetchAlerts(): Promise<AlertsResponse | null> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://forkast-api-511464604796.us-central1.run.app'}/api/v1/alerts`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      throw new Error('Failed to fetch alerts');
    }

    return res.json();
  } catch (error) {
    console.error('Alerts fetch error:', error);
    return null;
  }
}

export default async function AlertsPage() {
  const data = await fetchAlerts();

  if (!data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800">Backend Unavailable</h2>
          <p className="text-red-600 mt-2">
            Unable to connect to the backend server.
          </p>
        </div>
      </div>
    );
  }

  const { alerts, unacknowledged_count, total_count } = data;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Price Alerts</h1>
          <p className="text-gray-500 mt-1">
            AI-powered recommendations when competitors change prices
          </p>
        </div>
        {unacknowledged_count > 0 && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
            {unacknowledged_count} unread
          </span>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Alerts</p>
          <p className="text-2xl font-bold text-gray-900">{total_count}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Requires Review</p>
          <p className="text-2xl font-bold text-amber-600">{unacknowledged_count}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Reviewed</p>
          <p className="text-2xl font-bold text-forkast-green-600">{total_count - unacknowledged_count}</p>
        </div>
      </div>

      {/* Alerts List with Actionable Cards */}
      {alerts.length > 0 ? (
        <AlertsList initialAlerts={alerts} />
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-forkast-green-100 flex items-center justify-center mb-4">
            <svg className="h-6 w-6 text-forkast-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900">All Caught Up!</h3>
          <p className="text-gray-500 mt-2 max-w-sm mx-auto">
            No price alerts yet. Alerts are generated when competitors change prices by more than 5%.
          </p>
          <div className="mt-6">
            <Link
              href="/competitors"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-forkast-green-600 hover:text-forkast-green-700"
            >
              View Competitors
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>
        </div>
      )}

      {/* Pricing Strategy Insight */}
      {alerts.length > 0 && (
        <div className="bg-gradient-to-r from-forkast-green-50 to-emerald-50 border border-forkast-green-200 rounded-lg p-5">
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-10 h-10 bg-forkast-green-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-forkast-green-800">Pricing Strategy Insight</h4>
              <p className="text-sm text-forkast-green-700 mt-1">
                {alerts.filter(a => a.alert_type === 'price_increase').length > alerts.filter(a => a.alert_type === 'price_decrease').length
                  ? "Market trend: Competitors are raising prices. This signals potential room to increase your margins while remaining competitive. Focus on value messaging."
                  : "Market trend: Competitors are lowering prices. Rather than engaging in a price war, differentiate through quality, portion size, or unique offerings."}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Dashboard Home Page - Server Component

interface CategoryBreakdown {
  category: string;
  your_avg: number | string | null;
  market_avg: number | string | null;
  delta: number | string | null;
  items_compared: number;
}

interface DashboardComparison {
  market_average: number | string | null;
  total_competitors: number;
  recent_alerts_count: number;
  category_breakdown: CategoryBreakdown[];
}

// Helper to safely format numbers (handles string/null values from API)
function formatPrice(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return '0.00';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return isNaN(num) ? '0.00' : num.toFixed(2);
}

function formatPercent(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return '0.0';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return isNaN(num) ? '0.0' : num.toFixed(1);
}

function toNumber(value: number | string | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return isNaN(num) ? 0 : num;
}

async function fetchDashboardData(): Promise<DashboardComparison | null> {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/v1/dashboard/comparison', {
      cache: 'no-store',
    });

    if (!res.ok) {
      throw new Error('Failed to fetch dashboard data');
    }

    return res.json();
  } catch (error) {
    console.error('Dashboard fetch error:', error);
    return null;
  }
}

export default async function DashboardPage() {
  const data = await fetchDashboardData();

  if (!data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800">Backend Unavailable</h2>
          <p className="text-red-600 mt-2">
            Unable to connect to the backend server. Please ensure it&apos;s running at http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Monitor your competitive positioning in real-time</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Market Position Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <p className="text-sm font-medium text-gray-500">Market Position</p>
          <p className="text-3xl font-bold text-blue-600 mt-1">
            ${formatPrice(data.market_average)}
          </p>
          <p className="text-xs text-gray-400 mt-1">Market average price</p>
        </div>

        {/* Competitors Tracked Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <p className="text-sm font-medium text-gray-500">Competitors Tracked</p>
          <p className="text-3xl font-bold text-emerald-600 mt-1">
            {data.total_competitors}
          </p>
          <p className="text-xs text-gray-400 mt-1">Active competitors</p>
        </div>

        {/* Unread Alerts Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <p className="text-sm font-medium text-gray-500">Unread Alerts</p>
          <p className="text-3xl font-bold text-amber-600 mt-1">
            {data.recent_alerts_count}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {data.recent_alerts_count > 0 ? 'Requires attention' : 'All caught up'}
          </p>
        </div>
      </div>

      {/* Category Breakdown Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Category Breakdown</h2>
          <p className="text-sm text-gray-500 mt-1">Your pricing compared to market average by category</p>
        </div>

        {data.category_breakdown && data.category_breakdown.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="py-3 px-6 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="py-3 px-6 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Your Avg
                  </th>
                  <th className="py-3 px-6 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Market Avg
                  </th>
                  <th className="py-3 px-6 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Delta
                  </th>
                  <th className="py-3 px-6 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Items
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.category_breakdown.map((cat) => {
                  const deltaNum = toNumber(cat.delta);
                  return (
                    <tr key={cat.category}>
                      <td className="py-4 px-6 text-sm font-medium text-gray-900">
                        {cat.category}
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-600 text-right">
                        ${formatPrice(cat.your_avg)}
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-600 text-right">
                        ${formatPrice(cat.market_avg)}
                      </td>
                      <td className={`py-4 px-6 text-sm font-medium text-right ${
                        deltaNum > 0 ? 'text-red-600' : deltaNum < 0 ? 'text-green-600' : 'text-gray-500'
                      }`}>
                        {deltaNum > 0 ? '+' : ''}{formatPercent(cat.delta)}%
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-500 text-right">
                        {cat.items_compared}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center">
            <p className="text-gray-500">No category data available yet.</p>
            <p className="text-sm text-gray-400 mt-1">Add competitors to start tracking market prices.</p>
          </div>
        )}
      </div>
    </div>
  );
}

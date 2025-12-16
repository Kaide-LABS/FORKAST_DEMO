// Dashboard Home Page - Server Component

import PriceHistoryChart from '@/components/PriceHistoryChart';
import CategoryBreakdown from '@/components/CategoryBreakdown';
import ROICalculator from '@/components/ROICalculator';

interface CategoryBreakdownData {
  category: string;
  client_avg: number | string | null;
  market_avg: number | string | null;
  delta: number | string | null;
  items_compared: number;
}

interface DashboardComparison {
  market_average: number | string | null;
  total_competitors: number;
  recent_alerts_count: number;
  category_breakdown: CategoryBreakdownData[];
}

// Helper to safely format price values
function formatPrice(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return '0.00';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return isNaN(num) ? '0.00' : num.toFixed(2);
}

async function fetchDashboardData(): Promise<DashboardComparison | null> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/v1/dashboard/comparison`, {
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
          <p className="text-3xl font-bold text-forkast-green-600 mt-1">
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

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Price History Chart - Takes 2 columns */}
        <div className="lg:col-span-2">
          <PriceHistoryChart
            title="Market Price Trends (30 Days)"
            days={30}
          />
        </div>

        {/* ROI Calculator - Takes 1 column */}
        <div className="lg:col-span-1">
          <ROICalculator
            marketAverage={typeof data.market_average === 'string' ? parseFloat(data.market_average) : data.market_average || 0}
            competitorsCount={data.total_competitors}
          />
        </div>
      </div>

      {/* Category Breakdown */}
      <CategoryBreakdown categories={data.category_breakdown} />
    </div>
  );
}

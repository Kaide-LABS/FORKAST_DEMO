// Dashboard Home Page - Server Component

import PriceHistoryChart from '@/components/PriceHistoryChart';
import CategoryComparison from '@/components/CategoryComparison';
import AIInsights from '@/components/AIInsights';
import ROICalculator from '@/components/ROICalculator';
import { SERVER_API_URL, getServerApiHeaders } from '@/lib/server-config';

interface CategoryBreakdownData {
  category: string;
  client_avg: number | string | null;
  market_avg: number | string | null;
  delta: number | string | null;
  items_compared: number;
}

interface OperatorComparison {
  operator_name: string;
  operator_avg_price: number | string;
  market_avg_price: number | string;
  price_difference: number | string;
  percentage_difference: number | string;
  underpriced_items: number;
  overpriced_items: number;
  competitive_items: number;
  total_items: number;
}

interface DashboardComparison {
  market_average: number | string | null;
  total_competitors: number;
  recent_alerts_count: number;
  category_breakdown: CategoryBreakdownData[];
  operator_comparison: OperatorComparison | null;
}

// Helper to safely format price values
function formatPrice(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return '0.00';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return isNaN(num) ? '0.00' : num.toFixed(2);
}

async function fetchDashboardData(): Promise<DashboardComparison | null> {
  try {
    const res = await fetch(`${SERVER_API_URL}/api/v1/dashboard/comparison`, {
      cache: 'no-store',
      headers: await getServerApiHeaders(),
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
            Unable to connect to the backend server. Please try again later.
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

      {/* Operator Comparison Banner (if profile exists) */}
      {data.operator_comparison && (
        <div className="bg-gradient-to-r from-forkast-green-500 to-emerald-500 rounded-xl shadow-sm p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{data.operator_comparison.operator_name}</h2>
              <p className="text-sm text-white/80">Your price position vs the market</p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold">
                ${formatPrice(data.operator_comparison.operator_avg_price)}
              </p>
              <p className={`text-sm ${parseFloat(data.operator_comparison.percentage_difference as string) < 0 ? 'text-amber-200' : 'text-white/80'}`}>
                {parseFloat(data.operator_comparison.percentage_difference as string) > 0 ? '+' : ''}
                {parseFloat(data.operator_comparison.percentage_difference as string).toFixed(1)}% vs market
              </p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-xs text-white/70">Your Items</p>
              <p className="text-xl font-bold">{data.operator_comparison.total_items}</p>
            </div>
            <div className="bg-amber-500/30 rounded-lg p-3">
              <p className="text-xs text-white/70">Underpriced</p>
              <p className="text-xl font-bold">{data.operator_comparison.underpriced_items}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-xs text-white/70">Competitive</p>
              <p className="text-xl font-bold">{data.operator_comparison.competitive_items}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-xs text-white/70">Overpriced</p>
              <p className="text-xl font-bold">{data.operator_comparison.overpriced_items}</p>
            </div>
          </div>
        </div>
      )}

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

      {/* AI Insights */}
      <AIInsights />

      {/* Category Price Comparison */}
      <CategoryComparison />
    </div>
  );
}

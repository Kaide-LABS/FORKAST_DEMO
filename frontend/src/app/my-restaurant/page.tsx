'use client';

import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS } from '@/lib/config';

interface OperatorProfile {
  id: string;
  restaurant_name: string;
  location: string | null;
  concept_type: string | null;
  ubereats_url: string | null;
  doordash_url: string | null;
  monthly_orders: number | null;
  average_order_value: string | null;
  profit_margin: string | null;
  last_scraped_at: string | null;
  created_at: string;
  updated_at: string;
  menu_items: OperatorMenuItem[];
}

interface OperatorMenuItem {
  id: string;
  platform: string;
  name: string;
  category: string | null;
  current_price: string;
  is_available: boolean;
}

interface PriceGap {
  operator_item_name: string;
  operator_price: string;
  competitor_avg_price: string;
  price_difference: string;
  percentage_difference: string;
  opportunity_type: 'underpriced' | 'overpriced' | 'competitive';
  matching_competitors: number;
}

interface PriceAnalysis {
  operator_avg_price: string;
  market_avg_price: string;
  total_items_compared: number;
  underpriced_items: number;
  overpriced_items: number;
  competitive_items: number;
  potential_revenue_increase: string;
  price_gaps: PriceGap[];
}

export default function MyRestaurantPage() {
  const [profile, setProfile] = useState<OperatorProfile | null>(null);
  const [priceAnalysis, setPriceAnalysis] = useState<PriceAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    restaurant_name: '',
    location: '',
    concept_type: '',
    ubereats_url: '',
    doordash_url: '',
    monthly_orders: '',
    average_order_value: '',
    profit_margin: '',
  });

  const fetchProfile = useCallback(async () => {
    try {
      const res = await fetch(`${API_ENDPOINTS.operator}/profile`);
      if (res.ok) {
        const data = await res.json();
        if (data) {
          setProfile(data);
          setFormData({
            restaurant_name: data.restaurant_name || '',
            location: data.location || '',
            concept_type: data.concept_type || '',
            ubereats_url: data.ubereats_url || '',
            doordash_url: data.doordash_url || '',
            monthly_orders: data.monthly_orders?.toString() || '',
            average_order_value: data.average_order_value || '',
            profit_margin: data.profit_margin || '',
          });
        }
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchPriceAnalysis = useCallback(async () => {
    try {
      const res = await fetch(`${API_ENDPOINTS.operator}/price-analysis`);
      if (res.ok) {
        const data = await res.json();
        setPriceAnalysis(data);
      }
    } catch (err) {
      console.error('Error fetching price analysis:', err);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  useEffect(() => {
    if (profile?.menu_items?.length) {
      fetchPriceAnalysis();
    }
  }, [profile?.menu_items?.length, fetchPriceAnalysis]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const method = profile ? 'PUT' : 'POST';
      const payload = {
        restaurant_name: formData.restaurant_name,
        location: formData.location || null,
        concept_type: formData.concept_type || null,
        ubereats_url: formData.ubereats_url || null,
        doordash_url: formData.doordash_url || null,
        monthly_orders: formData.monthly_orders ? parseInt(formData.monthly_orders) : null,
        average_order_value: formData.average_order_value ? parseFloat(formData.average_order_value) : null,
        profit_margin: formData.profit_margin ? parseFloat(formData.profit_margin) : null,
      };

      const res = await fetch(`${API_ENDPOINTS.operator}/profile`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to save profile');
      }

      setSuccessMessage('Profile saved successfully!');
      await fetchProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const handleScrape = async (platform: 'ubereats' | 'doordash') => {
    setScraping(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const res = await fetch(`${API_ENDPOINTS.operator}/scrape?platform=${platform}`, {
        method: 'POST',
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to start scraping');
      }

      setSuccessMessage(`Scraping ${platform} menu in background. Refresh in a moment to see results.`);

      // Poll for completion
      setTimeout(async () => {
        await fetchProfile();
        await fetchPriceAnalysis();
        setScraping(false);
      }, 10000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scrape menu');
      setScraping(false);
    }
  };

  const formatPrice = (price: string | number) => {
    const num = typeof price === 'string' ? parseFloat(price) : price;
    return `$${num.toFixed(2)}`;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">My Restaurant</h1>
        <div className="animate-pulse bg-white rounded-xl p-6 border border-gray-200">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Restaurant</h1>
        <p className="text-gray-500 mt-1">
          Set up your restaurant profile to compare your prices with competitors
        </p>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800">{successMessage}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile Form */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Restaurant Profile</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Restaurant Name *
              </label>
              <input
                type="text"
                value={formData.restaurant_name}
                onChange={(e) => setFormData({ ...formData, restaurant_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location
                </label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500"
                  placeholder="e.g., New York, NY"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Concept Type
                </label>
                <input
                  type="text"
                  value={formData.concept_type}
                  onChange={(e) => setFormData({ ...formData, concept_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500"
                  placeholder="e.g., Italian, Fast Casual"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Uber Eats URL
              </label>
              <input
                type="url"
                value={formData.ubereats_url}
                onChange={(e) => setFormData({ ...formData, ubereats_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500"
                placeholder="https://www.ubereats.com/store/..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                DoorDash URL
              </label>
              <input
                type="url"
                value={formData.doordash_url}
                onChange={(e) => setFormData({ ...formData, doordash_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500"
                placeholder="https://www.doordash.com/store/..."
              />
            </div>

            <div className="border-t border-gray-200 pt-4 mt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Business Metrics (for ROI calculation)</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Monthly Orders
                  </label>
                  <input
                    type="number"
                    value={formData.monthly_orders}
                    onChange={(e) => setFormData({ ...formData, monthly_orders: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500"
                    placeholder="1000"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Avg Order Value ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.average_order_value}
                    onChange={(e) => setFormData({ ...formData, average_order_value: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500"
                    placeholder="25"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    Profit Margin (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.profit_margin}
                    onChange={(e) => setFormData({ ...formData, profit_margin: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500"
                    placeholder="15"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full px-4 py-2 bg-forkast-green-500 text-white rounded-lg font-medium hover:bg-forkast-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </form>
        </div>

        {/* Scraping & Menu */}
        <div className="space-y-6">
          {/* Scrape Controls */}
          {profile && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Scrape Your Menu</h2>
              <p className="text-sm text-gray-600 mb-4">
                Fetch your current menu and prices from your delivery platform listings.
              </p>

              <div className="flex gap-3">
                {profile.ubereats_url && (
                  <button
                    onClick={() => handleScrape('ubereats')}
                    disabled={scraping}
                    className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {scraping ? 'Scraping...' : 'Scrape Uber Eats'}
                  </button>
                )}
                {profile.doordash_url && (
                  <button
                    onClick={() => handleScrape('doordash')}
                    disabled={scraping}
                    className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {scraping ? 'Scraping...' : 'Scrape DoorDash'}
                  </button>
                )}
              </div>

              {profile.last_scraped_at && (
                <p className="text-xs text-gray-500 mt-3">
                  Last scraped: {formatDate(profile.last_scraped_at)}
                </p>
              )}
            </div>
          )}

          {/* Menu Items Preview */}
          {profile?.menu_items && profile.menu_items.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Your Menu ({profile.menu_items.length} items)
              </h2>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {profile.menu_items.slice(0, 10).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">{item.name}</p>
                      {item.category && (
                        <p className="text-xs text-gray-500">{item.category}</p>
                      )}
                    </div>
                    <span className="text-sm font-semibold text-forkast-green-600">
                      {formatPrice(item.current_price)}
                    </span>
                  </div>
                ))}
                {profile.menu_items.length > 10 && (
                  <p className="text-xs text-gray-500 text-center pt-2">
                    + {profile.menu_items.length - 10} more items
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Price Analysis Section */}
      {priceAnalysis && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-forkast-green-500 to-emerald-500 px-6 py-4">
            <h2 className="text-lg font-semibold text-white">Price Analysis vs Competitors</h2>
            <p className="text-sm text-white/80">See how your prices compare to the market</p>
          </div>

          <div className="p-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500">Your Avg Price</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatPrice(priceAnalysis.operator_avg_price)}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500">Market Avg Price</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatPrice(priceAnalysis.market_avg_price)}
                </p>
              </div>
              <div className="bg-amber-50 rounded-lg p-4">
                <p className="text-xs font-medium text-amber-700">Underpriced Items</p>
                <p className="text-xl font-bold text-amber-600">
                  {priceAnalysis.underpriced_items}
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-xs font-medium text-green-700">Potential Revenue+</p>
                <p className="text-xl font-bold text-green-600">
                  {formatPrice(priceAnalysis.potential_revenue_increase)}
                </p>
              </div>
            </div>

            {/* Price Gaps Table */}
            {priceAnalysis.price_gaps.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Price Opportunities</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Your Price</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Market Avg</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Difference</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {priceAnalysis.price_gaps.slice(0, 10).map((gap, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-900">{gap.operator_item_name}</td>
                          <td className="px-4 py-3 text-sm text-right text-gray-900">
                            {formatPrice(gap.operator_price)}
                          </td>
                          <td className="px-4 py-3 text-sm text-right text-gray-600">
                            {formatPrice(gap.competitor_avg_price)}
                          </td>
                          <td className={`px-4 py-3 text-sm text-right font-medium ${
                            parseFloat(gap.percentage_difference) < 0 ? 'text-amber-600' :
                            parseFloat(gap.percentage_difference) > 0 ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {parseFloat(gap.percentage_difference) > 0 ? '+' : ''}{parseFloat(gap.percentage_difference).toFixed(1)}%
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                              gap.opportunity_type === 'underpriced'
                                ? 'bg-amber-100 text-amber-700'
                                : gap.opportunity_type === 'overpriced'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-green-100 text-green-700'
                            }`}>
                              {gap.opportunity_type}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {priceAnalysis.price_gaps.length > 10 && (
                  <p className="text-xs text-gray-500 text-center mt-3">
                    Showing 10 of {priceAnalysis.price_gaps.length} items
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* No Profile Yet */}
      {!profile && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-800 mb-2">Get Started</h3>
          <p className="text-blue-700">
            Fill in your restaurant details above and add your Uber Eats URL to start comparing
            your prices with competitors. This will help you identify pricing opportunities and
            calculate your potential ROI.
          </p>
        </div>
      )}
    </div>
  );
}

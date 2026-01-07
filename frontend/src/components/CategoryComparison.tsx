'use client';

import { useState, useEffect } from 'react';

interface CategoryComparisonData {
  canonical_category_name: string;
  canonical_category_id: string;
  operator_avg: string | null;
  market_avg: string | null;
  delta_pct: string | null;
  operator_items: number;
  market_items: number;
}

interface ComparisonResponse {
  comparisons: CategoryComparisonData[];
  unmapped_operator_categories: string[];
  unmapped_competitor_categories: string[];
}

function formatPrice(price: string | null): string {
  if (price === null || price === undefined) return '—';
  const num = parseFloat(price);
  return isNaN(num) ? '—' : `$${num.toFixed(2)}`;
}

function formatPct(pct: string | null): string {
  if (pct === null || pct === undefined) return '—';
  const num = parseFloat(pct);
  if (isNaN(num)) return '—';
  const sign = num > 0 ? '+' : '';
  return `${sign}${num.toFixed(1)}%`;
}

function parseDelta(pct: string | null): number | null {
  if (pct === null || pct === undefined) return null;
  const num = parseFloat(pct);
  return isNaN(num) ? null : num;
}

export default function CategoryComparison() {
  const [data, setData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchComparison() {
      try {
        const res = await fetch('/api/proxy/api/v1/categories/comparison');
        if (!res.ok) throw new Error('Failed to fetch comparison');
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }
    fetchComparison();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  if (!data) return null;

  const hasComparisons = data.comparisons.some(c => c.operator_avg !== null && c.market_avg !== null);
  const unmappedCount = data.unmapped_operator_categories.length + data.unmapped_competitor_categories.length;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Category Price Comparison</h2>
          <p className="text-sm text-gray-500 mt-1">
            Your prices vs. market average by semantic category
          </p>
        </div>
        {unmappedCount > 0 && (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
            {unmappedCount} unmapped
          </span>
        )}
      </div>

      {!hasComparisons ? (
        <div className="text-center py-8 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
          </svg>
          <p className="font-medium">No comparison data yet</p>
          <p className="text-sm mt-1">Map categories for both your restaurant and competitors to see comparisons.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Comparison Cards */}
          <div className="grid gap-4">
            {data.comparisons
              .filter(c => c.operator_avg !== null || c.market_avg !== null)
              .map((comp) => {
                const hasFullComparison = comp.operator_avg !== null && comp.market_avg !== null;
                const delta = parseDelta(comp.delta_pct);
                const isHigher = delta !== null && delta > 0;
                const isLower = delta !== null && delta < 0;
                const operatorAvgNum = comp.operator_avg ? parseFloat(comp.operator_avg) : 0;
                const marketAvgNum = comp.market_avg ? parseFloat(comp.market_avg) : 0;
                const maxAvg = Math.max(operatorAvgNum, marketAvgNum);

                return (
                  <div
                    key={comp.canonical_category_id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-medium text-gray-900">{comp.canonical_category_name}</h3>
                      {hasFullComparison && (
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            isHigher
                              ? 'bg-red-100 text-red-700'
                              : isLower
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {isHigher ? '↑' : isLower ? '↓' : '='} {formatPct(comp.delta_pct)}
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500 mb-1">Your Avg</p>
                        <p className="font-semibold text-gray-900 text-lg">
                          {formatPrice(comp.operator_avg)}
                        </p>
                        <p className="text-xs text-gray-400">
                          {comp.operator_items} items
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500 mb-1">Market Avg</p>
                        <p className="font-semibold text-gray-900 text-lg">
                          {formatPrice(comp.market_avg)}
                        </p>
                        <p className="text-xs text-gray-400">
                          {comp.market_items} items
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500 mb-1">Difference</p>
                        <p
                          className={`font-semibold text-lg ${
                            isHigher
                              ? 'text-red-600'
                              : isLower
                              ? 'text-green-600'
                              : 'text-gray-900'
                          }`}
                        >
                          {formatPct(comp.delta_pct)}
                        </p>
                      </div>
                    </div>

                    {/* Visual bar comparison */}
                    {hasFullComparison && maxAvg > 0 && (
                      <div className="mt-4 pt-3 border-t border-gray-100">
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-gray-500 w-16">You</span>
                          <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-forkast-green-500 h-full rounded-full"
                              style={{
                                width: `${Math.min(100, (operatorAvgNum / maxAvg) * 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-xs mt-1">
                          <span className="text-gray-500 w-16">Market</span>
                          <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-gray-400 h-full rounded-full"
                              style={{
                                width: `${Math.min(100, (marketAvgNum / maxAvg) * 100)}%`,
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
          </div>

          {/* Summary Stats */}
          {hasComparisons && (
            <div className="bg-gray-50 rounded-lg p-4 mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Summary</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Higher than market</p>
                  <p className="font-semibold text-red-600">
                    {data.comparisons.filter(c => {
                      const d = parseDelta(c.delta_pct);
                      return d !== null && d > 0;
                    }).length} categories
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Lower than market</p>
                  <p className="font-semibold text-green-600">
                    {data.comparisons.filter(c => {
                      const d = parseDelta(c.delta_pct);
                      return d !== null && d < 0;
                    }).length} categories
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Need mapping</p>
                  <p className="font-semibold text-amber-600">
                    {unmappedCount} categories
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Unmapped Categories Warning */}
      {(data.unmapped_operator_categories.length > 0 || data.unmapped_competitor_categories.length > 0) && (
        <div className="border-t border-gray-200 pt-4">
          <h4 className="text-sm font-medium text-amber-700 mb-2">Unmapped Categories</h4>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            {data.unmapped_operator_categories.length > 0 && (
              <div>
                <p className="text-gray-500 mb-1">Your Restaurant:</p>
                <div className="flex flex-wrap gap-1">
                  {data.unmapped_operator_categories.map((cat) => (
                    <span
                      key={cat}
                      className="inline-flex px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-xs"
                    >
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {data.unmapped_competitor_categories.length > 0 && (
              <div>
                <p className="text-gray-500 mb-1">Competitors:</p>
                <div className="flex flex-wrap gap-1">
                  {data.unmapped_competitor_categories.map((cat) => (
                    <span
                      key={cat}
                      className="inline-flex px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-xs"
                    >
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Map these categories to enable full price comparison across all items.
          </p>
        </div>
      )}
    </div>
  );
}

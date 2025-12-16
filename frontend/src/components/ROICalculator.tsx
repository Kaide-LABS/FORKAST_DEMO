'use client';

import { useState, useEffect } from 'react';

interface ROICalculatorProps {
  marketAverage?: number;
  competitorsCount?: number;
}

export default function ROICalculator({ marketAverage = 0, competitorsCount = 0 }: ROICalculatorProps) {
  // Input state
  const [monthlyOrders, setMonthlyOrders] = useState<string>('1000');
  // Use market average as default AOV if available, otherwise use $25
  const [averageOrderValue, setAverageOrderValue] = useState<string>(
    marketAverage > 0 ? marketAverage.toFixed(0) : '25'
  );
  const [currentMargin, setCurrentMargin] = useState<string>('15');
  const [priceOptimization, setPriceOptimization] = useState<string>('3');

  // Calculated values
  const [potentialRevenue, setPotentialRevenue] = useState(0);
  const [potentialProfit, setPotentialProfit] = useState(0);
  const [annualImpact, setAnnualImpact] = useState(0);

  useEffect(() => {
    const orders = parseFloat(monthlyOrders) || 0;
    const aov = parseFloat(averageOrderValue) || 0;
    const margin = parseFloat(currentMargin) || 0;
    const optimization = parseFloat(priceOptimization) || 0;

    // Current monthly revenue
    const currentRevenue = orders * aov;

    // New AOV after optimization
    const newAOV = aov * (1 + optimization / 100);

    // New monthly revenue
    const newRevenue = orders * newAOV;

    // Additional revenue from price optimization
    const additionalRevenue = newRevenue - currentRevenue;

    // Additional profit (assuming same margin applies)
    const additionalProfit = additionalRevenue * (margin / 100);

    // Annual impact
    const annual = additionalProfit * 12;

    setPotentialRevenue(additionalRevenue);
    setPotentialProfit(additionalProfit);
    setAnnualImpact(annual);
  }, [monthlyOrders, averageOrderValue, currentMargin, priceOptimization]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-forkast-green-500 to-emerald-500 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">ROI Calculator</h3>
            <p className="text-sm text-white/80">Estimate your pricing optimization impact</p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Input Fields */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Monthly Orders
            </label>
            <input
              type="number"
              value={monthlyOrders}
              onChange={(e) => setMonthlyOrders(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
              placeholder="1000"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Avg Order Value ($)
            </label>
            <input
              type="number"
              value={averageOrderValue}
              onChange={(e) => setAverageOrderValue(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
              placeholder="25"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Current Margin (%)
            </label>
            <input
              type="number"
              value={currentMargin}
              onChange={(e) => setCurrentMargin(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
              placeholder="15"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Price Optimization (%)
            </label>
            <div className="relative">
              <input
                type="range"
                min="1"
                max="10"
                step="0.5"
                value={priceOptimization}
                onChange={(e) => setPriceOptimization(e.target.value)}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-forkast-green-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>1%</span>
                <span className="font-medium text-forkast-green-600">{priceOptimization}%</span>
                <span>10%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="border-t border-gray-100 pt-6">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
            Projected Impact
          </h4>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Additional Monthly Revenue</span>
              <span className="text-sm font-semibold text-gray-900">
                {formatCurrency(potentialRevenue)}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Additional Monthly Profit</span>
              <span className="text-sm font-semibold text-forkast-green-600">
                {formatCurrency(potentialProfit)}
              </span>
            </div>

            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-forkast-green-50 to-emerald-50 rounded-lg border border-forkast-green-200">
              <div>
                <span className="text-sm font-medium text-forkast-green-800">Annual Profit Impact</span>
                <p className="text-xs text-forkast-green-600 mt-0.5">
                  With {competitorsCount} competitors tracked
                </p>
              </div>
              <span className="text-2xl font-bold text-forkast-green-600">
                {formatCurrency(annualImpact)}
              </span>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
            </svg>
            <div className="text-sm">
              <p className="font-medium text-amber-800">
                Industry benchmark: 3-5% price optimization
              </p>
              <p className="text-amber-700 mt-1">
                Restaurants using competitive intelligence typically achieve 3-5% better pricing compared to those who don&apos;t monitor competitors.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS } from '@/lib/config';

interface ROICalculatorProps {
  marketAverage?: number;
  competitorsCount?: number;
}

interface PriceGap {
  operator_item_name: string;
  operator_price: string;
  competitor_avg_price: string;
  percentage_difference: string;
  opportunity_type: string;
}

interface ROIData {
  monthly_orders: number;
  average_order_value: string;
  profit_margin: string;
  current_monthly_revenue: string;
  potential_price_increase_pct: string;
  additional_monthly_revenue: string;
  additional_monthly_profit: string;
  annual_impact: string;
  forkast_monthly_cost: string;
  forkast_annual_cost: string;
  net_annual_roi: string;
  roi_multiple: string;
  underpriced_items_count: number;
  avg_underpricing_pct: string;
  top_opportunities: PriceGap[];
}

// Restaurant presets
const PRESETS = {
  small: { name: 'Small Restaurant', orders: 500, aov: 22, margin: 12 },
  medium: { name: 'Medium Restaurant', orders: 1500, aov: 28, margin: 15 },
  high_volume: { name: 'High Volume', orders: 4000, aov: 35, margin: 18 },
};

export default function ROICalculator({ marketAverage = 0, competitorsCount = 0 }: ROICalculatorProps) {
  // Input state
  const [monthlyOrders, setMonthlyOrders] = useState<string>('1000');
  const [averageOrderValue, setAverageOrderValue] = useState<string>(
    marketAverage > 0 ? marketAverage.toFixed(0) : '25'
  );
  const [currentMargin, setCurrentMargin] = useState<string>('15');
  const [priceOptimization, setPriceOptimization] = useState<string>('3');
  const [forkastCost, setForkastCost] = useState<string>('99');
  const [activePreset, setActivePreset] = useState<string | null>(null);

  // API data
  const [roiData, setRoiData] = useState<ROIData | null>(null);
  const [hasOperatorProfile, setHasOperatorProfile] = useState(false);
  const [loadingRoi, setLoadingRoi] = useState(false);

  // Calculated values (local calculation as fallback)
  const [potentialRevenue, setPotentialRevenue] = useState(0);
  const [potentialProfit, setPotentialProfit] = useState(0);
  const [annualImpact, setAnnualImpact] = useState(0);

  // Check if operator profile exists
  useEffect(() => {
    const checkProfile = async () => {
      try {
        const res = await fetch(`${API_ENDPOINTS.operator}/profile`);
        if (res.ok) {
          const data = await res.json();
          if (data) {
            setHasOperatorProfile(true);
            // Pre-fill with operator data if available
            if (data.monthly_orders) setMonthlyOrders(data.monthly_orders.toString());
            if (data.average_order_value) setAverageOrderValue(data.average_order_value);
            if (data.profit_margin) setCurrentMargin(data.profit_margin);
          }
        }
      } catch (err) {
        console.error('Error checking operator profile:', err);
      }
    };
    checkProfile();
  }, []);

  // Fetch ROI analysis from API when inputs change
  const fetchROIAnalysis = useCallback(async () => {
    if (!hasOperatorProfile) return;

    setLoadingRoi(true);
    try {
      const params = new URLSearchParams({
        monthly_orders: monthlyOrders || '1000',
        average_order_value: averageOrderValue || '25',
        profit_margin: currentMargin || '15',
        forkast_monthly_cost: forkastCost || '99',
      });

      const res = await fetch(`${API_ENDPOINTS.operator}/roi-analysis?${params}`);
      if (res.ok) {
        const data = await res.json();
        setRoiData(data);
        // Update optimization percentage based on actual data
        if (data.potential_price_increase_pct) {
          setPriceOptimization(parseFloat(data.potential_price_increase_pct).toFixed(1));
        }
      }
    } catch (err) {
      console.error('Error fetching ROI analysis:', err);
    } finally {
      setLoadingRoi(false);
    }
  }, [hasOperatorProfile, monthlyOrders, averageOrderValue, currentMargin, forkastCost]);

  // Debounced API call
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchROIAnalysis();
    }, 500);
    return () => clearTimeout(timer);
  }, [fetchROIAnalysis]);

  // Local calculation (fallback when no API data)
  useEffect(() => {
    const orders = parseFloat(monthlyOrders) || 0;
    const aov = parseFloat(averageOrderValue) || 0;
    const margin = parseFloat(currentMargin) || 0;
    const optimization = parseFloat(priceOptimization) || 0;

    const currentRevenue = orders * aov;
    const newAOV = aov * (1 + optimization / 100);
    const newRevenue = orders * newAOV;
    const additionalRevenue = newRevenue - currentRevenue;
    const additionalProfit = additionalRevenue * (margin / 100);
    const annual = additionalProfit * 12;

    setPotentialRevenue(additionalRevenue);
    setPotentialProfit(additionalProfit);
    setAnnualImpact(annual);
  }, [monthlyOrders, averageOrderValue, currentMargin, priceOptimization]);

  const applyPreset = (presetKey: string) => {
    const preset = PRESETS[presetKey as keyof typeof PRESETS];
    if (preset) {
      setMonthlyOrders(preset.orders.toString());
      setAverageOrderValue(preset.aov.toString());
      setCurrentMargin(preset.margin.toString());
      setActivePreset(presetKey);
    }
  };

  const formatCurrency = (value: number | string) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  const generatePDFReport = () => {
    // Create a simple printable report
    const reportData = roiData || {
      monthly_orders: monthlyOrders,
      average_order_value: averageOrderValue,
      profit_margin: currentMargin,
      additional_monthly_revenue: potentialRevenue.toFixed(2),
      additional_monthly_profit: potentialProfit.toFixed(2),
      annual_impact: annualImpact.toFixed(2),
      forkast_monthly_cost: forkastCost,
      forkast_annual_cost: (parseFloat(forkastCost) * 12).toFixed(2),
      net_annual_roi: (annualImpact - parseFloat(forkastCost) * 12).toFixed(2),
      roi_multiple: (annualImpact / (parseFloat(forkastCost) * 12)).toFixed(1),
      potential_price_increase_pct: priceOptimization,
      underpriced_items_count: 0,
      top_opportunities: [],
    };

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Forkast ROI Report</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
          h1 { color: #10b981; border-bottom: 2px solid #10b981; padding-bottom: 10px; }
          h2 { color: #374151; margin-top: 30px; }
          .summary { background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
          .stat { background: white; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; }
          .stat-label { font-size: 12px; color: #6b7280; text-transform: uppercase; }
          .stat-value { font-size: 24px; font-weight: bold; color: #10b981; }
          .highlight { background: #ecfdf5; border-color: #10b981; }
          table { width: 100%; border-collapse: collapse; margin: 20px 0; }
          th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
          th { background: #f9fafb; font-size: 12px; color: #6b7280; text-transform: uppercase; }
          .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; }
          @media print { body { padding: 20px; } }
        </style>
      </head>
      <body>
        <h1>Forkast ROI Analysis Report</h1>
        <p>Generated on ${new Date().toLocaleDateString()}</p>

        <h2>Business Inputs</h2>
        <div class="grid">
          <div class="stat">
            <div class="stat-label">Monthly Orders</div>
            <div class="stat-value">${parseInt(reportData.monthly_orders as string).toLocaleString()}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Average Order Value</div>
            <div class="stat-value">${formatCurrency(reportData.average_order_value)}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Profit Margin</div>
            <div class="stat-value">${reportData.profit_margin}%</div>
          </div>
          <div class="stat">
            <div class="stat-label">Price Optimization</div>
            <div class="stat-value">${reportData.potential_price_increase_pct}%</div>
          </div>
        </div>

        <h2>Projected Impact</h2>
        <div class="grid">
          <div class="stat">
            <div class="stat-label">Additional Monthly Revenue</div>
            <div class="stat-value">${formatCurrency(reportData.additional_monthly_revenue)}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Additional Monthly Profit</div>
            <div class="stat-value">${formatCurrency(reportData.additional_monthly_profit)}</div>
          </div>
          <div class="stat highlight">
            <div class="stat-label">Annual Profit Impact</div>
            <div class="stat-value">${formatCurrency(reportData.annual_impact)}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Underpriced Items Found</div>
            <div class="stat-value">${reportData.underpriced_items_count}</div>
          </div>
        </div>

        <h2>Forkast ROI</h2>
        <div class="summary">
          <div class="grid">
            <div>
              <p><strong>Forkast Annual Cost:</strong> ${formatCurrency(reportData.forkast_annual_cost)}</p>
              <p><strong>Net Annual ROI:</strong> ${formatCurrency(reportData.net_annual_roi)}</p>
            </div>
            <div>
              <p><strong>ROI Multiple:</strong> ${reportData.roi_multiple}x</p>
              <p>For every $1 spent on Forkast, you get $${reportData.roi_multiple} back in additional profit.</p>
            </div>
          </div>
        </div>

        ${(reportData.top_opportunities as PriceGap[]).length > 0 ? `
        <h2>Top Pricing Opportunities</h2>
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Your Price</th>
              <th>Market Avg</th>
              <th>Gap</th>
            </tr>
          </thead>
          <tbody>
            ${(reportData.top_opportunities as PriceGap[]).map((gap: PriceGap) => `
              <tr>
                <td>${gap.operator_item_name}</td>
                <td>${formatCurrency(gap.operator_price)}</td>
                <td>${formatCurrency(gap.competitor_avg_price)}</td>
                <td>${parseFloat(gap.percentage_difference).toFixed(1)}%</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        ` : ''}

        <div class="footer">
          <p>This report was generated by Forkast Competitive Intelligence Dashboard.</p>
          <p>The projections are estimates based on the inputs provided and industry benchmarks.</p>
        </div>

        <script>window.print();</script>
      </body>
      </html>
    `);
    printWindow.document.close();
  };

  // Use API data if available, otherwise use local calculations
  const displayData = {
    additionalRevenue: roiData ? parseFloat(roiData.additional_monthly_revenue) : potentialRevenue,
    additionalProfit: roiData ? parseFloat(roiData.additional_monthly_profit) : potentialProfit,
    annualImpact: roiData ? parseFloat(roiData.annual_impact) : annualImpact,
    netRoi: roiData ? parseFloat(roiData.net_annual_roi) : (annualImpact - parseFloat(forkastCost) * 12),
    roiMultiple: roiData ? parseFloat(roiData.roi_multiple) : (annualImpact / (parseFloat(forkastCost) * 12)),
    underpricedCount: roiData?.underpriced_items_count || 0,
    avgUnderpricing: roiData ? parseFloat(roiData.avg_underpricing_pct) : 0,
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
            <p className="text-sm text-white/80">
              {hasOperatorProfile ? 'Based on your actual price data' : 'Estimate your pricing optimization impact'}
            </p>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Presets */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-500 mb-2">Quick Presets</label>
          <div className="flex gap-2">
            {Object.entries(PRESETS).map(([key, preset]) => (
              <button
                key={key}
                onClick={() => applyPreset(key)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                  activePreset === key
                    ? 'bg-forkast-green-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {preset.name}
              </button>
            ))}
          </div>
        </div>

        {/* Input Fields */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Monthly Orders
            </label>
            <input
              type="number"
              value={monthlyOrders}
              onChange={(e) => { setMonthlyOrders(e.target.value); setActivePreset(null); }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
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
              onChange={(e) => { setAverageOrderValue(e.target.value); setActivePreset(null); }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
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
              onChange={(e) => { setCurrentMargin(e.target.value); setActivePreset(null); }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
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

        {/* Price Gap Alert */}
        {hasOperatorProfile && displayData.underpricedCount > 0 && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-amber-800">
                  {displayData.underpricedCount} items priced below market
                </p>
                <p className="text-xs text-amber-700">
                  Average {displayData.avgUnderpricing.toFixed(1)}% below competitors
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        <div className="border-t border-gray-100 pt-6">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
            Projected Impact
          </h4>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Additional Monthly Revenue</span>
              <span className="text-sm font-semibold text-gray-900">
                {formatCurrency(displayData.additionalRevenue)}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Additional Monthly Profit</span>
              <span className="text-sm font-semibold text-forkast-green-600">
                {formatCurrency(displayData.additionalProfit)}
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
                {formatCurrency(displayData.annualImpact)}
              </span>
            </div>
          </div>
        </div>

        {/* Forkast ROI */}
        <div className="mt-6 pt-6 border-t border-gray-100">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">
            Forkast ROI
          </h4>

          <div className="flex items-center gap-2 mb-3">
            <label className="text-xs text-gray-500">Forkast monthly cost:</label>
            <div className="relative">
              <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400">$</span>
              <input
                type="number"
                value={forkastCost}
                onChange={(e) => setForkastCost(e.target.value)}
                className="w-20 pl-6 pr-2 py-1 border border-gray-300 rounded text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-forkast-green-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500">Annual Cost</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(parseFloat(forkastCost) * 12)}
              </p>
            </div>
            <div className="p-3 bg-forkast-green-50 rounded-lg border border-forkast-green-200">
              <p className="text-xs text-forkast-green-700">Net Annual ROI</p>
              <p className="text-lg font-bold text-forkast-green-600">
                {formatCurrency(displayData.netRoi)}
              </p>
            </div>
          </div>

          <div className="mt-3 p-3 bg-gradient-to-r from-emerald-500 to-forkast-green-500 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/90">ROI Multiple</p>
                <p className="text-xs text-white/70">For every $1 spent on Forkast</p>
              </div>
              <div className="text-right">
                <span className="text-3xl font-bold text-white">
                  {displayData.roiMultiple.toFixed(1)}x
                </span>
                <p className="text-xs text-white/80">return</p>
              </div>
            </div>
          </div>
        </div>

        {/* Download Report Button */}
        <button
          onClick={generatePDFReport}
          className="w-full mt-6 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Download ROI Report
        </button>

        {/* CTA */}
        <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
            </svg>
            <div className="text-sm">
              <p className="font-medium text-amber-800">
                Industry benchmark: 3-5% price optimization
              </p>
              <p className="text-amber-700 mt-1">
                {hasOperatorProfile
                  ? 'Your optimization % is calculated from your actual price gaps vs competitors.'
                  : 'Add your restaurant in "My Restaurant" to see your actual price opportunities.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

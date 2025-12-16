'use client';

import { useState } from 'react';

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

interface ActionableAlertCardProps {
  alert: Alert;
  onAcknowledge?: (id: string) => void;
}

// Format date to relative time
function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffHours / 24);

  if (diffHours < 1) return 'Just now';
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

  return date.toLocaleDateString();
}

// Parse price from string like "$12.99"
function parsePrice(value: string | null): number {
  if (!value) return 0;
  return parseFloat(value.replace(/[^0-9.]/g, '')) || 0;
}

// Generate recommendation based on alert type and magnitude
function generateRecommendation(alert: Alert): {
  primary: string;
  secondary: string;
  urgency: 'low' | 'medium' | 'high';
  actions: string[];
} {
  const changeNum = typeof alert.change_percentage === 'string'
    ? parseFloat(alert.change_percentage)
    : alert.change_percentage || 0;

  const absChange = Math.abs(changeNum);
  const isIncrease = alert.alert_type === 'price_increase';
  const oldPrice = parsePrice(alert.old_value);
  const newPrice = parsePrice(alert.new_value);
  const priceDiff = Math.abs(newPrice - oldPrice);

  if (isIncrease) {
    // Competitor raised prices
    if (absChange >= 15) {
      return {
        primary: `Significant price increase opportunity detected`,
        secondary: `${alert.competitor_name} raised this item by ${absChange.toFixed(0)}%. You may have room to increase your price while remaining competitive.`,
        urgency: 'high',
        actions: [
          `Consider raising your price by $${(priceDiff * 0.5).toFixed(2)} to capture margin`,
          'Monitor customer demand for 48 hours first',
          'Emphasize value-adds in your listing'
        ]
      };
    } else {
      return {
        primary: `Competitor raised prices`,
        secondary: `This could indicate market-wide cost pressures. Consider if a smaller adjustment is appropriate.`,
        urgency: 'medium',
        actions: [
          'Review your costs for this item',
          'Consider a modest price increase',
          'No immediate action needed'
        ]
      };
    }
  } else {
    // Competitor dropped prices
    if (absChange >= 15) {
      return {
        primary: `⚠️ Aggressive price drop - possible promotion`,
        secondary: `${alert.competitor_name} dropped this item by ${absChange.toFixed(0)}%. This is likely a temporary promotion rather than a permanent change.`,
        urgency: 'high',
        actions: [
          'Monitor for 48-72 hours before reacting',
          'Consider a bundle deal instead of matching',
          'Emphasize quality differentiators',
          'Do NOT match - could be a loss leader'
        ]
      };
    } else if (absChange >= 8) {
      return {
        primary: `Notable price reduction`,
        secondary: `You're now ${priceDiff.toFixed(2)} higher than ${alert.competitor_name} on this item.`,
        urgency: 'medium',
        actions: [
          'Evaluate if matching makes sense for your margins',
          'Consider adding value (larger portion, premium ingredient)',
          'Highlight your unique selling points'
        ]
      };
    } else {
      return {
        primary: `Minor price adjustment`,
        secondary: `Small competitive shift. Your positioning remains largely unchanged.`,
        urgency: 'low',
        actions: [
          'No immediate action recommended',
          'Continue monitoring trends',
          'Focus on quality and service'
        ]
      };
    }
  }
}

export default function ActionableAlertCard({ alert, onAcknowledge }: ActionableAlertCardProps) {
  const [isExpanded, setIsExpanded] = useState(!alert.is_acknowledged);
  const [selectedAction, setSelectedAction] = useState<number | null>(null);

  const isIncrease = alert.alert_type === 'price_increase';
  const changeNum = typeof alert.change_percentage === 'string'
    ? parseFloat(alert.change_percentage)
    : alert.change_percentage || 0;

  const recommendation = generateRecommendation(alert);

  const urgencyColors = {
    low: 'border-l-gray-400',
    medium: 'border-l-amber-500',
    high: 'border-l-red-500'
  };

  const handleAcknowledge = async () => {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/v1/alerts/${alert.id}/acknowledge`,
        { method: 'POST' }
      );
      onAcknowledge?.(alert.id);
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 border-l-4 ${urgencyColors[recommendation.urgency]} overflow-hidden transition-all ${
        !alert.is_acknowledged ? 'ring-2 ring-amber-200' : ''
      }`}
    >
      {/* Header - Always visible */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div
            className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
              isIncrease
                ? 'bg-red-100 text-red-600'
                : 'bg-green-100 text-green-600'
            }`}
          >
            {isIncrease ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
              </svg>
            )}
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-gray-900">
                {alert.competitor_name}
              </span>
              {!alert.is_acknowledged && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                  New
                </span>
              )}
              <span className="text-xs text-gray-500">
                {formatRelativeTime(alert.created_at)}
              </span>
            </div>

            <p className="mt-1 text-sm text-gray-700">
              <span className="font-medium">{alert.item_name}</span>
              {' '}
              <span className={isIncrease ? 'text-red-600' : 'text-green-600'}>
                {alert.old_value} → {alert.new_value}
              </span>
              {' '}
              <span className={`font-semibold ${isIncrease ? 'text-red-600' : 'text-green-600'}`}>
                ({changeNum > 0 ? '+' : ''}{changeNum.toFixed(1)}%)
              </span>
            </p>

            <p className="mt-2 text-sm font-medium text-gray-800">
              {recommendation.primary}
            </p>
          </div>

          {/* Expand/Collapse Icon */}
          <div className="flex-shrink-0">
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          {/* Analysis */}
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Analysis
            </h4>
            <p className="text-sm text-gray-700">
              {recommendation.secondary}
            </p>
          </div>

          {/* Recommended Actions */}
          <div className="mt-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Recommended Actions
            </h4>
            <div className="space-y-2">
              {recommendation.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedAction(selectedAction === index ? null : index)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-3 ${
                    selectedAction === index
                      ? 'bg-forkast-green-100 text-forkast-green-800 border border-forkast-green-300'
                      : 'bg-white border border-gray-200 text-gray-700 hover:border-forkast-green-300 hover:bg-forkast-green-50'
                  }`}
                >
                  <span className={`flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                    selectedAction === index
                      ? 'border-forkast-green-500 bg-forkast-green-500'
                      : 'border-gray-300'
                  }`}>
                    {selectedAction === index && (
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </span>
                  {action}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-4 flex gap-3">
            {!alert.is_acknowledged && (
              <button
                onClick={handleAcknowledge}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-forkast-green-500 rounded-lg hover:bg-forkast-green-600 transition-colors"
              >
                Mark as Reviewed
              </button>
            )}
            <button
              onClick={() => setIsExpanded(false)}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Collapse
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

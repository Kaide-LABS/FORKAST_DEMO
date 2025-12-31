'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
  ReferenceLine,
} from 'recharts';
import { API_BASE_URL } from '@/lib/config';

interface PricePoint {
  date: string;
  price: number;
}

interface ItemPriceHistory {
  item_id: string;
  item_name: string;
  competitor_id: string;
  competitor_name: string;
  data: PricePoint[];
}

interface PriceHistoryResponse {
  items: ItemPriceHistory[];
  start_date: string;
  end_date: string;
}

interface PriceHistoryChartProps {
  competitorId?: string;
  itemIds?: string[];
  days?: number;
  title?: string;
  initialCategory?: string;
}

interface TooltipPayload {
  name: string;
  value: number;
  color: string;
  payload: Record<string, unknown>;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

// Color palette for multiple lines - distinct colors for competitors
const COMPETITOR_COLORS: Record<string, string> = {};
const COLOR_PALETTE = [
  '#00C853', // green (Brand color)
  '#F59E0B', // amber
  '#EF4444', // red
  '#8B5CF6', // purple
  '#06B6D4', // cyan
  '#EC4899', // pink
  '#F97316', // orange
  '#3B82F6', // blue
  '#10B981', // emerald
  '#6366F1', // indigo
];

function getCompetitorColor(competitorName: string): string {
  if (!COMPETITOR_COLORS[competitorName]) {
    const index = Object.keys(COMPETITOR_COLORS).length % COLOR_PALETTE.length;
    COMPETITOR_COLORS[competitorName] = COLOR_PALETTE[index];
  }
  return COMPETITOR_COLORS[competitorName];
}

export default function PriceHistoryChart({
  competitorId,
  itemIds,
  days = 30,
  title = 'Price History',
  initialCategory,
}: PriceHistoryChartProps) {
  const [data, setData] = useState<PriceHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedCompetitors, setSelectedCompetitors] = useState<Set<string>>(new Set());
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('all');
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>(initialCategory || '');
  const [itemsPerCompetitor, setItemsPerCompetitor] = useState<number>(10);
  const [competitorIds, setCompetitorIds] = useState<Record<string, string>>({});
  const containerRef = useRef<HTMLDivElement>(null);
  const competitorIdsRef = useRef<Record<string, string>>({});

  // Check if viewing all competitors or a specific one
  const isAllCompetitorsView = !competitorId;

  // Determine which competitor ID to use for categories (from prop or tab selection)
  const activeCompetitorId = competitorId || (activeTab !== 'all' ? competitorIds[activeTab] : null);

  // Get unique competitors from data
  const competitors = data?.items
    ? Array.from(new Set(data.items.map((item) => item.competitor_name)))
    : [];

  // Fetch available categories - for specific competitor views (either via prop or tab selection)
  useEffect(() => {
    const fetchCategories = async () => {
      // Only fetch categories when viewing a specific competitor
      if (!activeCompetitorId) {
        setCategories([]);
        setSelectedCategory('');
        return;
      }

      try {
        const url = `${API_BASE_URL}/api/v1/dashboard/categories?competitor_id=${activeCompetitorId}`;
        const response = await fetch(url);
        if (response.ok) {
          const cats = await response.json();
          setCategories(cats);
        }
      } catch (err) {
        console.error('Failed to fetch categories:', err);
      }
    };
    fetchCategories();
  }, [activeCompetitorId]);

  useEffect(() => {
    const fetchPriceHistory = async () => {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        params.append('days', days.toString());

        // Determine if we're viewing a specific competitor (use ref to avoid stale closure)
        const targetCompetitorId = competitorId || competitorIdsRef.current[activeTab];
        const isSpecificCompetitor = !!targetCompetitorId;

        // For all competitors view, use items_per_competitor
        // For specific competitor (via prop or tab), use regular limit
        if (!isSpecificCompetitor) {
          params.append('limit_per_competitor', itemsPerCompetitor.toString());
        } else {
          params.append('limit', '20');
          params.append('competitor_id', targetCompetitorId);
        }

        if (itemIds && itemIds.length > 0) {
          params.append('item_ids', itemIds.join(','));
        }

        // Apply category filter when viewing a specific competitor
        if (selectedCategory && isSpecificCompetitor) {
          params.append('category', selectedCategory);
        }

        const response = await fetch(
          `${API_BASE_URL}/api/v1/dashboard/price-history?${params.toString()}`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch price history');
        }

        const result: PriceHistoryResponse = await response.json();
        setData(result);

        // Build competitor ID map from results (for tab switching)
        const idMap: Record<string, string> = {};
        result.items.forEach((item) => {
          if (!idMap[item.competitor_name]) {
            idMap[item.competitor_name] = item.competitor_id;
          }
        });
        // Update both ref (for immediate use) and state (for re-renders)
        competitorIdsRef.current = { ...competitorIdsRef.current, ...idMap };
        setCompetitorIds(competitorIdsRef.current);

        // Initialize all competitors as selected
        if (result.items.length > 0) {
          const allCompetitors = new Set(result.items.map((item) => item.competitor_name));
          setSelectedCompetitors(allCompetitors);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchPriceHistory();
  }, [competitorId, itemIds, days, selectedCategory, activeTab, itemsPerCompetitor]);

  // Fullscreen toggle logic
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement && containerRef.current) {
      containerRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch(() => {
        setIsFullscreen(true); // Fallback
      });
    } else if (document.fullscreenElement) {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    } else {
      setIsFullscreen(!isFullscreen);
    }
  }, [isFullscreen]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen && !document.fullscreenElement) {
        setIsFullscreen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  // Filter logic
  const toggleCompetitor = (competitor: string) => {
    setSelectedCompetitors((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(competitor)) {
        if (newSet.size > 1) newSet.delete(competitor);
      } else {
        newSet.add(competitor);
      }
      return newSet;
    });
  };

  const selectAllCompetitors = () => {
    setSelectedCompetitors(new Set(competitors));
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="h-80 flex items-center justify-center">
          <div className="flex items-center gap-2 text-gray-500">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Loading chart data...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="h-80 flex items-center justify-center">
          <div className="text-red-500 text-center">
            <p>Error loading data: {error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="h-80 flex items-center justify-center">
          <div className="text-gray-500 text-center">
            <p>No price history data available</p>
          </div>
        </div>
      </div>
    );
  }

  const filteredItems = data.items.filter((item) => {
    if (activeTab === 'all') {
      return selectedCompetitors.has(item.competitor_name);
    }
    return item.competitor_name === activeTab;
  });

  // Data processing for Recharts
  const allDates = new Set<string>();
  filteredItems.forEach((item) => {
    item.data.forEach((point) => allDates.add(point.date));
  });

  const sortedDates = Array.from(allDates).sort();

  const chartData = sortedDates.map((date) => {
    const point: Record<string, string | number> = { date };
    filteredItems.forEach((item) => {
      const pricePoint = item.data.find((p) => p.date === date);
      if (pricePoint) {
        const key = `${item.competitor_name}: ${item.item_name}`;
        point[key] = pricePoint.price;
      }
    });
    return point;
  });

  const allPrices = filteredItems.flatMap((item) => item.data.map((p) => p.price));
  const avgPrice = allPrices.length > 0
    ? allPrices.reduce((a, b) => a + b, 0) / allPrices.length
    : 0;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  // Get latest price for an item
  const getLatestPrice = (itemKey: string): number | null => {
    const item = filteredItems.find(
      (i) => `${i.competitor_name}: ${i.item_name}` === itemKey
    );
    if (item && item.data.length > 0) {
      return item.data[item.data.length - 1].price;
    }
    return null;
  };

  // Custom Legend with hover tooltips (only in fullscreen)
  const CustomLegend = ({ payload }: { payload?: Array<{ value: string; color: string }> }) => {
    const [hoveredItem, setHoveredLegendItem] = useState<string | null>(null);

    if (!payload) return null;

    return (
      <div className="flex flex-wrap justify-center gap-3 pt-5 px-4">
        {payload.map((entry, index) => {
          const price = getLatestPrice(entry.value);
          const isHovered = hoveredItem === entry.value;

          return (
            <div
              key={index}
              className="relative inline-flex items-center gap-1.5 cursor-pointer group"
              onMouseEnter={() => setHoveredLegendItem(entry.value)}
              onMouseLeave={() => setHoveredLegendItem(null)}
            >
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-xs text-gray-600 group-hover:text-gray-900">
                {entry.value}
              </span>

              {/* Price tooltip on hover */}
              {isHovered && price !== null && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg whitespace-nowrap z-50">
                  <div className="font-medium">{entry.value}</div>
                  <div className="text-forkast-green-400 font-bold text-lg">${price.toFixed(2)}</div>
                  <div className="text-gray-400 text-xs">Current price</div>
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 shadow-lg rounded-lg border border-gray-100 text-sm z-50">
          <p className="font-semibold text-gray-700 mb-2 border-b pb-1">{label}</p>
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {payload.map((entry, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className="text-gray-600 truncate max-w-[150px]">{entry.name}</span>
                <span className="font-mono font-medium ml-auto">${Number(entry.value).toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  const chartHeight = isFullscreen ? 'calc(100vh - 200px)' : '350px';

  const ChartContent = () => (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-500 mt-1">
            Trends from <span className="font-medium text-gray-700">{data.start_date}</span> to <span className="font-medium text-gray-700">{data.end_date}</span>
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Items Per Competitor Dropdown - Only for All Competitors tab (no specific competitor selected) */}
          {!activeCompetitorId && (
            <div className="relative">
              <select
                value={itemsPerCompetitor}
                onChange={(e) => setItemsPerCompetitor(Number(e.target.value))}
                className="appearance-none bg-white border border-gray-200 rounded-lg px-4 py-2 pr-8 text-sm font-medium text-gray-700 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent cursor-pointer"
              >
                <option value={5}>5 items/competitor</option>
                <option value={10}>10 items/competitor</option>
                <option value={20}>20 items/competitor</option>
                <option value={50}>50 items/competitor</option>
                <option value={100}>100 items/competitor</option>
              </select>
              <svg
                className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          )}

          {/* Category Filter Dropdown - Show when a specific competitor is selected (via prop or tab) */}
          {categories.length > 0 && activeCompetitorId && (
            <div className="relative">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="appearance-none bg-white border border-gray-200 rounded-lg px-4 py-2 pr-8 text-sm font-medium text-gray-700 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent cursor-pointer"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
              <svg
                className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          )}

          <button
            onClick={toggleFullscreen}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-all"
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Modern Tabs / Pills - Only show on dashboard (not on individual competitor pages) */}
      {isAllCompetitorsView && competitors.length > 0 && (
        <div className="mb-6">
          <div className="flex flex-wrap gap-2 p-1 bg-gray-50 rounded-xl border border-gray-100 overflow-x-auto w-full">
            <button
              onClick={() => setActiveTab('all')}
              className={`
                px-4 py-2 text-sm font-medium rounded-lg transition-all whitespace-nowrap
                ${activeTab === 'all'
                  ? 'bg-white text-gray-900 shadow-sm ring-1 ring-gray-200'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'}
              `}
            >
              All Competitors
            </button>
            {competitors.map((competitor) => (
              <button
                key={competitor}
                onClick={() => setActiveTab(competitor)}
                className={`
                  px-4 py-2 text-sm font-medium rounded-lg transition-all whitespace-nowrap
                  ${activeTab === competitor
                    ? 'bg-white text-gray-900 shadow-sm ring-1 ring-gray-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'}
                `}
              >
                {competitor}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filter Chips (Only in 'All' view on dashboard) */}
      {isAllCompetitorsView && competitors.length > 1 && activeTab === 'all' && (
        <div className="mb-4 flex flex-wrap gap-2 items-center">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider mr-1">Filter</span>
          <button
            onClick={selectAllCompetitors}
            className={`px-3 py-1 text-xs font-medium rounded-full border transition-colors ${
               selectedCompetitors.size === competitors.length
                ? 'bg-gray-800 text-white border-gray-800'
                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
            }`}
          >
            Select All
          </button>
          {competitors.map((competitor) => {
            const isSelected = selectedCompetitors.has(competitor);
            const color = getCompetitorColor(competitor);
            return (
              <button
                key={competitor}
                onClick={() => toggleCompetitor(competitor)}
                className={`
                  px-3 py-1 text-xs font-medium rounded-full border transition-all flex items-center gap-1.5
                  ${isSelected ? 'bg-white shadow-sm' : 'bg-gray-50 opacity-60'}
                `}
                style={{
                  borderColor: isSelected ? color : 'transparent',
                  color: isSelected ? '#1f2937' : '#9ca3af',
                }}
              >
                <span className={`w-2 h-2 rounded-full ${isSelected ? '' : 'grayscale'}`} style={{ backgroundColor: color }} />
                {competitor}
              </button>
            );
          })}
        </div>
      )}

      <div style={{ height: chartHeight }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#9ca3af' }}
              dy={10}
            />
            <YAxis
              tickFormatter={(val) => `$${val}`}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#9ca3af' }}
              domain={['auto', 'auto']}
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#e5e7eb', strokeWidth: 1 }} />
            {/* Show legend if 15 or fewer items, OR if in fullscreen mode (user can scroll) */}
            {(filteredItems.length <= 15 || isFullscreen) && (
              <Legend
                content={isFullscreen ? <CustomLegend /> : undefined}
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="circle"
              />
            )}
            {avgPrice > 0 && (
               <ReferenceLine y={avgPrice} stroke="#cbd5e1" strokeDasharray="3 3" label={{ position: 'insideTopRight', value: 'Avg', fill: '#94a3b8', fontSize: 10 }} />
            )}
            <Brush dataKey="date" height={20} stroke="#e2e8f0" fill="#f8fafc" tickFormatter={() => ''} />
            
            {filteredItems.map((item) => {
              const key = `${item.competitor_name}: ${item.item_name}`;
              const color = getCompetitorColor(item.competitor_name);
              const isHovered = hoveredItem === key;

              return (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={color}
                  strokeWidth={isHovered ? 3 : 2}
                  dot={{ r: 4, fill: color, strokeWidth: 0 }}
                  activeDot={{ r: 6, strokeWidth: 0 }}
                  onMouseEnter={() => setHoveredItem(key)}
                  onMouseLeave={() => setHoveredItem(null)}
                  connectNulls
                  animationDuration={800}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Show summary when legend is hidden due to many items (not in fullscreen) */}
      {filteredItems.length > 15 && !isFullscreen && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-100">
          <p className="text-sm text-gray-600">
            <span className="font-medium">{filteredItems.length} items</span> displayed from{' '}
            <span className="font-medium">{competitors.length} competitor{competitors.length !== 1 ? 's' : ''}</span>.
            Hover over the chart to see item details.
          </p>
          <button
            onClick={toggleFullscreen}
            className="mt-2 inline-flex items-center gap-2 text-sm text-forkast-green-600 hover:text-forkast-green-700 font-medium"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            Go fullscreen to see all item details (scroll down)
          </button>
        </div>
      )}
    </>
  );

  if (isFullscreen && !document.fullscreenElement) {
    return (
      <>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 min-h-[400px] flex items-center justify-center">
          <div className="text-center text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            <p>Viewing in Fullscreen</p>
          </div>
        </div>
        <div className="fixed inset-0 z-[100] bg-white overflow-y-auto">
          <div ref={containerRef} className="max-w-7xl mx-auto p-6 min-h-screen">
             <ChartContent />
          </div>
        </div>
      </>
    );
  }

  return (
    <div ref={containerRef} className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 transition-all ${isFullscreen ? 'fixed inset-0 z-50 overflow-auto rounded-none' : ''}`}>
      <ChartContent />
    </div>
  );
}
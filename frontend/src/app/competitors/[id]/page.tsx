// Competitor Details Page - Server Component

import Link from 'next/link';
import { notFound } from 'next/navigation';
import RefreshDataButton from '@/components/RefreshDataButton';

interface Competitor {
  id: string;
  name: string;
  location: string;
  concept_type: string;
  doordash_url: string | null;
  ubereats_url: string | null;
  scraping_enabled: boolean;
  last_scraped_at: string | null;
}

interface MenuItem {
  id: string;
  name: string;
  category: string | null;
  description: string | null;
  current_price: string | number;
  is_available: boolean;
  menu_position: number | null;
}

// Format date consistently
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// Format price safely
function formatPrice(price: string | number | null): string {
  if (price === null || price === undefined) return '$0.00';
  const num = typeof price === 'string' ? parseFloat(price) : price;
  return isNaN(num) ? '$0.00' : `$${num.toFixed(2)}`;
}

// Group menu items by category
function groupByCategory(items: MenuItem[]): Record<string, MenuItem[]> {
  return items.reduce((groups, item) => {
    const category = item.category || 'Other';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(item);
    return groups;
  }, {} as Record<string, MenuItem[]>);
}

async function fetchCompetitor(id: string): Promise<Competitor | null> {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/v1/competitors/${id}`, {
      cache: 'no-store',
    });

    if (res.status === 404) {
      return null;
    }

    if (!res.ok) {
      throw new Error('Failed to fetch competitor');
    }

    return res.json();
  } catch (error) {
    console.error('Competitor fetch error:', error);
    return null;
  }
}

async function fetchMenuItems(id: string): Promise<MenuItem[]> {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/v1/competitors/${id}/menu`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      return [];
    }

    return res.json();
  } catch (error) {
    console.error('Menu items fetch error:', error);
    return [];
  }
}

export default async function CompetitorDetailsPage({
  params,
}: {
  params: { id: string };
}) {
  const [competitor, menuItems] = await Promise.all([
    fetchCompetitor(params.id),
    fetchMenuItems(params.id),
  ]);

  if (!competitor) {
    notFound();
  }

  const groupedItems = groupByCategory(menuItems);
  const categories = Object.keys(groupedItems).sort();

  return (
    <div className="space-y-8">
      {/* Back Link */}
      <Link
        href="/competitors"
        className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18"
          />
        </svg>
        Back to Competitors
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{competitor.name}</h1>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  competitor.scraping_enabled
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {competitor.scraping_enabled ? 'Active' : 'Paused'}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
              <span className="inline-flex items-center gap-1">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
                </svg>
                {competitor.location}
              </span>
              {competitor.concept_type && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-50 text-blue-700">
                  {competitor.concept_type}
                </span>
              )}
            </div>
            {competitor.last_scraped_at && (
              <p className="mt-2 text-xs text-gray-400">
                Last updated: {formatDate(competitor.last_scraped_at)}
              </p>
            )}
          </div>

          {/* Action Bar */}
          <div className="flex items-center gap-3">
            <RefreshDataButton competitorId={competitor.id} />
            {competitor.doordash_url && (
              <a
                href={competitor.doordash_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
                DoorDash
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Menu Stats */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex flex-wrap gap-6 text-sm">
          <div>
            <span className="text-gray-500">Total Items: </span>
            <span className="font-medium text-gray-900">{menuItems.length}</span>
          </div>
          <div>
            <span className="text-gray-500">Categories: </span>
            <span className="font-medium text-gray-900">{categories.length}</span>
          </div>
          {menuItems.length > 0 && (
            <div>
              <span className="text-gray-500">Avg Price: </span>
              <span className="font-medium text-gray-900">
                {formatPrice(
                  menuItems.reduce((sum, item) => {
                    const price = typeof item.current_price === 'string'
                      ? parseFloat(item.current_price)
                      : item.current_price;
                    return sum + (isNaN(price) ? 0 : price);
                  }, 0) / menuItems.length
                )}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Menu Items */}
      {menuItems.length > 0 ? (
        <div className="space-y-6">
          {categories.map((category) => (
            <div key={category} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              {/* Category Header */}
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">{category}</h2>
                <p className="text-sm text-gray-500">{groupedItems[category].length} items</p>
              </div>

              {/* Items Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="py-3 px-6 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Item
                      </th>
                      <th className="py-3 px-6 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">
                        Description
                      </th>
                      <th className="py-3 px-6 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Price
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {groupedItems[category].map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900">
                              {item.name}
                            </span>
                            {!item.is_available && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                                Unavailable
                              </span>
                            )}
                          </div>
                          {/* Show description on mobile */}
                          {item.description && (
                            <p className="mt-1 text-xs text-gray-500 md:hidden line-clamp-2">
                              {item.description}
                            </p>
                          )}
                        </td>
                        <td className="py-4 px-6 hidden md:table-cell">
                          <p className="text-sm text-gray-500 max-w-md truncate">
                            {item.description || '-'}
                          </p>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <span className="text-sm font-medium text-gray-900">
                            {formatPrice(item.current_price)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900">No menu items yet</h3>
          <p className="text-gray-500 mt-2 max-w-sm mx-auto">
            Click the button below to fetch menu data for this competitor.
          </p>
          <div className="mt-6">
            <RefreshDataButton competitorId={competitor.id} />
          </div>
        </div>
      )}
    </div>
  );
}

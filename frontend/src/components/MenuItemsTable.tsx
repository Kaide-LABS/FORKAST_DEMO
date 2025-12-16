'use client';

import { useState, useMemo, useCallback } from 'react';

interface MenuItem {
  id: string;
  name: string;
  category: string | null;
  description: string | null;
  current_price: string | number;
  is_available: boolean;
  menu_position: number | null;
}

interface MenuItemsTableProps {
  items: MenuItem[];
  competitorName?: string;
}

type SortField = 'name' | 'price' | 'category';
type SortOrder = 'asc' | 'desc';

// Format price safely
function formatPrice(price: string | number | null): string {
  if (price === null || price === undefined) return '$0.00';
  const num = typeof price === 'string' ? parseFloat(price) : price;
  return isNaN(num) ? '$0.00' : `$${num.toFixed(2)}`;
}

function getPrice(price: string | number | null): number {
  if (price === null || price === undefined) return 0;
  const num = typeof price === 'string' ? parseFloat(price) : price;
  return isNaN(num) ? 0 : num;
}

// Escape CSV field (handle commas, quotes, newlines)
function escapeCSV(field: string | null | undefined): string {
  if (field === null || field === undefined) return '';
  const str = String(field);
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export default function MenuItemsTable({ items, competitorName = 'Menu' }: MenuItemsTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set<string>();
    items.forEach((item) => {
      cats.add(item.category || 'Other');
    });
    return Array.from(cats).sort();
  }, [items]);

  // Filter and sort items
  const filteredItems = useMemo(() => {
    let result = [...items];

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (item) =>
          item.name.toLowerCase().includes(query) ||
          (item.description && item.description.toLowerCase().includes(query))
      );
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      result = result.filter(
        (item) => (item.category || 'Other') === selectedCategory
      );
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'price':
          comparison = getPrice(a.current_price) - getPrice(b.current_price);
          break;
        case 'category':
          comparison = (a.category || 'Other').localeCompare(b.category || 'Other');
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [items, searchQuery, selectedCategory, sortField, sortOrder]);

  // Export to CSV
  const exportToCSV = useCallback(() => {
    // CSV Header
    const headers = ['Name', 'Category', 'Price', 'Description', 'Available'];

    // CSV Rows (use filtered items)
    const rows = filteredItems.map((item) => [
      escapeCSV(item.name),
      escapeCSV(item.category || 'Other'),
      getPrice(item.current_price).toFixed(2),
      escapeCSV(item.description),
      item.is_available ? 'Yes' : 'No',
    ]);

    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    // Generate filename with date
    const date = new Date().toISOString().split('T')[0];
    const filename = `${competitorName.replace(/[^a-z0-9]/gi, '_')}_menu_${date}.csv`;
    link.download = filename;

    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [filteredItems, competitorName]);

  // Handle sort click
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  // Sort indicator
  const SortIndicator = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return (
        <svg className="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 15 12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9" />
        </svg>
      );
    }
    return sortOrder === 'asc' ? (
      <svg className="h-4 w-4 text-forkast-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
      </svg>
    ) : (
      <svg className="h-4 w-4 text-forkast-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
      </svg>
    );
  };

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Search and Filter Bar */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search Input */}
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Search menu items..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                <svg className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Category Filter */}
          <div className="sm:w-48">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent bg-white"
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Export Button */}
          <button
            onClick={exportToCSV}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Export CSV
          </button>
        </div>

        {/* Results Count */}
        <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
          <span>
            Showing {filteredItems.length} of {items.length} items
          </span>
          {(searchQuery || selectedCategory !== 'all') && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory('all');
              }}
              className="text-forkast-green-600 hover:text-forkast-green-700 font-medium"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      {filteredItems.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/50">
                <th className="py-3 px-6 text-left">
                  <button
                    onClick={() => handleSort('name')}
                    className="flex items-center gap-1 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700"
                  >
                    Item
                    <SortIndicator field="name" />
                  </button>
                </th>
                <th className="py-3 px-6 text-left hidden lg:table-cell">
                  <button
                    onClick={() => handleSort('category')}
                    className="flex items-center gap-1 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700"
                  >
                    Category
                    <SortIndicator field="category" />
                  </button>
                </th>
                <th className="py-3 px-6 text-left hidden md:table-cell">
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Description
                  </span>
                </th>
                <th className="py-3 px-6 text-right">
                  <button
                    onClick={() => handleSort('price')}
                    className="flex items-center gap-1 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 ml-auto"
                  >
                    Price
                    <SortIndicator field="price" />
                  </button>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 transition-colors">
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
                    {/* Show category on mobile */}
                    <p className="mt-1 text-xs text-gray-500 lg:hidden">
                      {item.category || 'Other'}
                    </p>
                    {/* Show description on mobile */}
                    {item.description && (
                      <p className="mt-1 text-xs text-gray-400 md:hidden line-clamp-2">
                        {item.description}
                      </p>
                    )}
                  </td>
                  <td className="py-4 px-6 hidden lg:table-cell">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                      {item.category || 'Other'}
                    </span>
                  </td>
                  <td className="py-4 px-6 hidden md:table-cell">
                    <p className="text-sm text-gray-500 max-w-md truncate">
                      {item.description || '-'}
                    </p>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <span className="text-sm font-semibold text-gray-900">
                      {formatPrice(item.current_price)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="p-8 text-center">
          <svg className="h-12 w-12 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <p className="text-gray-500">No items match your search</p>
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedCategory('all');
            }}
            className="mt-2 text-forkast-green-600 hover:text-forkast-green-700 text-sm font-medium"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}

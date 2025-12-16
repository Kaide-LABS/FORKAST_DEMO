'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

// Format date consistently to avoid hydration mismatch
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

interface Competitor {
  id: string;
  name: string;
  location: string;
  concept_type: string;
  doordash_url: string | null;
  ubereats_url: string | null;
  scraping_enabled: boolean;
  last_scraped_at: string | null;
  items_count?: number;
}

interface CompetitorCardProps {
  competitor: Competitor;
}

export default function CompetitorCard({ competitor }: CompetitorCardProps) {
  const router = useRouter();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleRefreshData = async () => {
    setIsRefreshing(true);
    setMessage(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/v1/scraping/trigger/${competitor.id}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to refresh data');
      }

      const data = await response.json();
      setMessage({
        type: 'success',
        text: `Menu updated! ${data.items_count} items loaded.`,
      });

      // Refresh the page data after a brief delay
      setTimeout(() => {
        router.refresh();
      }, 1500);
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to refresh data',
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <Link
              href={`/competitors/${competitor.id}`}
              className="text-lg font-semibold text-gray-900 hover:text-forkast-green-600 transition-colors"
            >
              {competitor.name}
            </Link>
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
          <p className="text-sm text-gray-500 mt-1">{competitor.location}</p>
        </div>
      </div>

      {/* Item Count */}
      <div className="mt-3 flex items-center gap-2">
        <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-sm font-medium bg-indigo-50 text-indigo-700">
          {competitor.items_count ?? 0} items tracked
        </span>
      </div>

      {/* Message Toast */}
      {message && (
        <div
          className={`mt-3 p-3 rounded-lg text-sm ${
            message.type === 'success'
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-forkast-green-50 text-forkast-green-700">
            {competitor.concept_type || 'Uncategorized'}
          </span>
          <div className="flex gap-2">
            {competitor.doordash_url && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
                DoorDash
              </span>
            )}
            {competitor.ubereats_url && (
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
                Uber Eats
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-4 flex gap-2">
          <Link
            href={`/competitors/${competitor.id}`}
            className="flex-1 inline-flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
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
                d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
              />
            </svg>
            View Menu
          </Link>
          <button
            onClick={handleRefreshData}
            disabled={isRefreshing}
            className="flex-1 inline-flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-forkast-green-500 rounded-lg hover:bg-forkast-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRefreshing ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Refreshing...
              </>
            ) : (
              <>
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
                    d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
                  />
                </svg>
                Refresh
              </>
            )}
          </button>
        </div>

        {/* Last Scraped */}
        {competitor.last_scraped_at && (
          <p className="mt-3 text-xs text-gray-400">
            Last updated:{' '}
            {formatDate(competitor.last_scraped_at)}
          </p>
        )}
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface RefreshDataButtonProps {
  competitorId: string;
  variant?: 'primary' | 'secondary';
  className?: string;
}

export default function RefreshDataButton({
  competitorId,
  variant = 'primary',
  className = '',
}: RefreshDataButtonProps) {
  const router = useRouter();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setMessage(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/scraping/trigger/${competitorId}`,
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
        setMessage(null);
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

  const baseStyles = 'inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
  const variantStyles = variant === 'primary'
    ? 'bg-blue-600 text-white hover:bg-blue-700'
    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50';

  return (
    <div className="relative">
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className={`${baseStyles} ${variantStyles} ${className}`}
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
            Refresh Data
          </>
        )}
      </button>

      {/* Toast Message */}
      {message && (
        <div
          className={`absolute top-full left-0 right-0 mt-2 p-3 rounded-lg text-sm whitespace-nowrap ${
            message.type === 'success'
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
}

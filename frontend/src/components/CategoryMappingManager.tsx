'use client';

import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS } from '@/lib/config';

interface CanonicalCategory {
  id: string;
  name: string;
  description: string | null;
  keywords: string | null;
}

interface CategoryMapping {
  id: string;
  source_type: string;
  source_id: string;
  raw_category: string;
  canonical_category_id: string;
  canonical_category: CanonicalCategory | null;
  confidence_score: string | null;
  is_manual: boolean;
}

interface CategorySuggestion {
  raw_category: string;
  canonical_category_id: string;
  canonical_category_name: string;
  confidence_score: number;
  alternatives: Array<{
    id: string;
    name: string;
    score: number;
  }>;
}

interface CategoryMappingManagerProps {
  sourceType: 'operator' | 'competitor';
  sourceId: string;
  rawCategories: string[];
  onMappingsChanged?: () => void;
}

export default function CategoryMappingManager({
  sourceType,
  sourceId,
  rawCategories,
  onMappingsChanged,
}: CategoryMappingManagerProps) {
  const [canonicalCategories, setCanonicalCategories] = useState<CanonicalCategory[]>([]);
  const [mappings, setMappings] = useState<CategoryMapping[]>([]);
  const [suggestions, setSuggestions] = useState<CategorySuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [savingCategory, setSavingCategory] = useState<string | null>(null);
  const [autoMapping, setAutoMapping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch canonical categories
  const fetchCanonicalCategories = useCallback(async () => {
    try {
      const res = await fetch(`${API_ENDPOINTS.categories}/canonical`);
      if (res.ok) {
        const data = await res.json();
        setCanonicalCategories(data);
      }
    } catch (err) {
      console.error('Error fetching canonical categories:', err);
    }
  }, []);

  // Fetch existing mappings
  const fetchMappings = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_ENDPOINTS.categories}/mappings?source_type=${sourceType}&source_id=${sourceId}`
      );
      if (res.ok) {
        const data = await res.json();
        setMappings(data);
      }
    } catch (err) {
      console.error('Error fetching mappings:', err);
    }
  }, [sourceType, sourceId]);

  // Fetch AI suggestions
  const fetchSuggestions = useCallback(async () => {
    setLoadingSuggestions(true);
    try {
      const res = await fetch(
        `${API_ENDPOINTS.categories}/suggest?source_type=${sourceType}&source_id=${sourceId}`
      );
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data);
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err);
    } finally {
      setLoadingSuggestions(false);
    }
  }, [sourceType, sourceId]);

  // Initial load
  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      await Promise.all([fetchCanonicalCategories(), fetchMappings()]);
      setLoading(false);
    };
    loadAll();
  }, [fetchCanonicalCategories, fetchMappings]);

  // Fetch suggestions after mappings are loaded
  useEffect(() => {
    if (!loading && rawCategories.length > 0) {
      fetchSuggestions();
    }
  }, [loading, rawCategories.length, fetchSuggestions]);

  // Create or update a mapping
  const saveMapping = async (rawCategory: string, canonicalCategoryId: string) => {
    setSavingCategory(rawCategory);
    setError(null);

    try {
      const res = await fetch(`${API_ENDPOINTS.categories}/mappings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: sourceType,
          source_id: sourceId,
          raw_category: rawCategory,
          canonical_category_id: canonicalCategoryId,
          is_manual: true,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to save mapping');
      }

      // Refresh mappings and suggestions
      await Promise.all([fetchMappings(), fetchSuggestions()]);
      onMappingsChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save mapping');
    } finally {
      setSavingCategory(null);
    }
  };

  // Auto-map all with high confidence
  const handleAutoMap = async () => {
    setAutoMapping(true);
    setError(null);

    try {
      const res = await fetch(
        `${API_ENDPOINTS.categories}/auto-map?source_type=${sourceType}&source_id=${sourceId}&threshold=0.75`,
        { method: 'POST' }
      );

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Auto-mapping failed');
      }

      const result = await res.json();

      // Refresh data
      await Promise.all([fetchMappings(), fetchSuggestions()]);
      onMappingsChanged?.();

      // Show result
      if (result.mapped > 0) {
        alert(`Successfully mapped ${result.mapped} categories!`);
      } else {
        alert('No categories met the confidence threshold for auto-mapping.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auto-mapping failed');
    } finally {
      setAutoMapping(false);
    }
  };

  // Get mapping for a raw category
  const getMappingFor = (rawCategory: string) => {
    return mappings.find((m) => m.raw_category === rawCategory);
  };

  // Get suggestion for a raw category
  const getSuggestionFor = (rawCategory: string) => {
    return suggestions.find((s) => s.raw_category === rawCategory);
  };

  // Format confidence as percentage
  const formatConfidence = (score: number | string | null) => {
    if (score === null) return null;
    const num = typeof score === 'string' ? parseFloat(score) : score;
    return `${(num * 100).toFixed(0)}%`;
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        <div className="h-24 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (rawCategories.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No menu categories found.</p>
        <p className="text-sm mt-1">Scrape your menu first to see categories.</p>
      </div>
    );
  }

  const mappedCount = rawCategories.filter((c) => getMappingFor(c)).length;
  const unmappedCount = rawCategories.length - mappedCount;

  return (
    <div className="space-y-6">
      {/* Header with stats */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Category Mappings</h3>
          <p className="text-sm text-gray-500 mt-1">
            Map your menu categories to standard categories for accurate comparison
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm">
            <span className="text-green-600 font-medium">{mappedCount} mapped</span>
            {unmappedCount > 0 && (
              <span className="text-amber-600 ml-2">{unmappedCount} unmapped</span>
            )}
          </div>
          {suggestions.length > 0 && (
            <button
              onClick={handleAutoMap}
              disabled={autoMapping}
              className="px-4 py-2 bg-forkast-green-500 text-white text-sm font-medium rounded-lg hover:bg-forkast-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {autoMapping ? 'Mapping...' : 'Auto-Map All'}
            </button>
          )}
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading suggestions indicator */}
      {loadingSuggestions && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700 flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Getting AI suggestions...
        </div>
      )}

      {/* Categories table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Your Category
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mapped To
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                AI Suggestion
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {rawCategories.map((rawCategory) => {
              const mapping = getMappingFor(rawCategory);
              const suggestion = getSuggestionFor(rawCategory);
              const isSaving = savingCategory === rawCategory;

              return (
                <tr key={rawCategory} className="hover:bg-gray-50">
                  {/* Raw category name */}
                  <td className="px-4 py-3">
                    <span className="font-medium text-gray-900">{rawCategory}</span>
                  </td>

                  {/* Current mapping */}
                  <td className="px-4 py-3">
                    {mapping ? (
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          {mapping.canonical_category?.name || 'Unknown'}
                        </span>
                        {mapping.is_manual && (
                          <span className="text-xs text-gray-400">manual</span>
                        )}
                        {!mapping.is_manual && mapping.confidence_score && (
                          <span className="text-xs text-gray-400">
                            {formatConfidence(mapping.confidence_score)}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                        Unmapped
                      </span>
                    )}
                  </td>

                  {/* AI suggestion */}
                  <td className="px-4 py-3">
                    {suggestion && !mapping ? (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-700">
                          {suggestion.canonical_category_name}
                        </span>
                        <span
                          className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                            suggestion.confidence_score >= 0.8
                              ? 'bg-green-100 text-green-700'
                              : suggestion.confidence_score >= 0.6
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {formatConfidence(suggestion.confidence_score)}
                        </span>
                      </div>
                    ) : mapping ? (
                      <span className="text-xs text-gray-400">-</span>
                    ) : (
                      <span className="text-xs text-gray-400">No suggestion</span>
                    )}
                  </td>

                  {/* Action */}
                  <td className="px-4 py-3 text-right">
                    {!mapping && suggestion ? (
                      <button
                        onClick={() =>
                          saveMapping(rawCategory, suggestion.canonical_category_id)
                        }
                        disabled={isSaving}
                        className="text-sm text-forkast-green-600 hover:text-forkast-green-700 font-medium disabled:opacity-50"
                      >
                        {isSaving ? 'Saving...' : 'Accept'}
                      </button>
                    ) : (
                      <select
                        value={mapping?.canonical_category_id || ''}
                        onChange={(e) => {
                          if (e.target.value) {
                            saveMapping(rawCategory, e.target.value);
                          }
                        }}
                        disabled={isSaving}
                        className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-forkast-green-500"
                      >
                        <option value="">Select category...</option>
                        {canonicalCategories.map((cat) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-green-100 border border-green-300"></span>
          <span>High confidence (80%+)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-yellow-100 border border-yellow-300"></span>
          <span>Medium confidence (60-80%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-gray-100 border border-gray-300"></span>
          <span>Low confidence (&lt;60%)</span>
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface AddCompetitorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AddCompetitorModal({ isOpen, onClose }: AddCompetitorModalProps) {
  const router = useRouter();

  // Form state
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [conceptType, setConceptType] = useState('');
  const [doordashUrl, setDoordashUrl] = useState('');
  const [ubereatsUrl, setUbereatsUrl] = useState('');

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetForm = () => {
    setName('');
    setLocation('');
    setConceptType('');
    setDoordashUrl('');
    setUbereatsUrl('');
    setError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/v1/competitors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          location: location || null,
          concept_type: conceptType || null,
          doordash_url: doordashUrl || null,
          ubereats_url: ubereatsUrl || null,
          scraping_enabled: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Failed to create competitor (${response.status})`);
      }

      // Success - close modal and refresh data
      handleClose();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Add New Competitor</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-500 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Competitor Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="e.g., Burger Palace"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
            />
          </div>

          {/* Location */}
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
              Location <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              required
              placeholder="e.g., 123 Main St, Austin TX"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
            />
          </div>

          {/* Concept Type */}
          <div>
            <label htmlFor="conceptType" className="block text-sm font-medium text-gray-700 mb-1">
              Concept Type
            </label>
            <select
              id="conceptType"
              value={conceptType}
              onChange={(e) => setConceptType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent bg-white"
            >
              <option value="">Select a type...</option>
              <option value="Burger">Burger</option>
              <option value="Pizza">Pizza</option>
              <option value="Mexican">Mexican</option>
              <option value="Asian">Asian</option>
              <option value="Italian">Italian</option>
              <option value="Casual Dining">Casual Dining</option>
              <option value="Fast Food">Fast Food</option>
              <option value="Seafood">Seafood</option>
              <option value="Other">Other</option>
            </select>
          </div>

          {/* DoorDash URL */}
          <div>
            <label htmlFor="doordashUrl" className="block text-sm font-medium text-gray-700 mb-1">
              DoorDash URL
            </label>
            <input
              type="url"
              id="doordashUrl"
              value={doordashUrl}
              onChange={(e) => setDoordashUrl(e.target.value)}
              placeholder="https://www.doordash.com/store/..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
            />
          </div>

          {/* Uber Eats URL */}
          <div>
            <label htmlFor="ubereatsUrl" className="block text-sm font-medium text-gray-700 mb-1">
              Uber Eats URL
            </label>
            <input
              type="url"
              id="ubereatsUrl"
              value={ubereatsUrl}
              onChange={(e) => setUbereatsUrl(e.target.value)}
              placeholder="https://www.ubereats.com/store/..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-forkast-green-500 focus:border-transparent"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2.5 bg-forkast-green-500 text-white text-sm font-medium rounded-lg hover:bg-forkast-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Submitting...
                </>
              ) : (
                'Add Competitor'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { API_BASE_URL } from '@/lib/config';
import { revalidateCompetitors } from '@/app/actions';

interface AddCompetitorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ModalState = 'form' | 'scraping' | 'success' | 'error';

export default function AddCompetitorModal({ isOpen, onClose }: AddCompetitorModalProps) {
  // Form state
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [conceptType, setConceptType] = useState('');
  const [doordashUrl, setDoordashUrl] = useState('');
  const [ubereatsUrl, setUbereatsUrl] = useState('');

  // UI state
  const [modalState, setModalState] = useState<ModalState>('form');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scrapingMessage, setScrapingMessage] = useState('');
  const [successData, setSuccessData] = useState<{ name: string; itemsCount: number } | null>(null);

  const resetForm = () => {
    setName('');
    setLocation('');
    setConceptType('');
    setDoordashUrl('');
    setUbereatsUrl('');
    setError(null);
    setModalState('form');
    setScrapingMessage('');
    setSuccessData(null);
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
      // Step 1: Create the competitor
      setScrapingMessage('Creating competitor...');

      const createResponse = await fetch(`${API_BASE_URL}/api/v1/competitors/`, {
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

      if (!createResponse.ok) {
        const errorData = await createResponse.json().catch(() => null);
        throw new Error(errorData?.detail || `Failed to create competitor (${createResponse.status})`);
      }

      const competitor = await createResponse.json();

      // Step 2: Check if we have a URL to scrape
      if (!ubereatsUrl && !doordashUrl) {
        // No URL provided, just show success without scraping
        setSuccessData({ name: competitor.name, itemsCount: 0 });
        setModalState('success');
        await revalidateCompetitors();
        return;
      }

      // Step 3: Trigger scraping
      setModalState('scraping');
      setScrapingMessage(`Scraping menu for ${name}... This may take 1-2 minutes.`);

      const scrapeResponse = await fetch(`${API_BASE_URL}/api/v1/scraping/trigger/${competitor.id}`, {
        method: 'POST',
      });

      if (!scrapeResponse.ok) {
        const errorData = await scrapeResponse.json().catch(() => null);
        // Scraping failed, but competitor was created
        setError(errorData?.detail || 'Scraping failed, but competitor was added. You can try scraping again later.');
        setModalState('error');
        await revalidateCompetitors();
        return;
      }

      const scrapeResult = await scrapeResponse.json();

      // Step 4: Show success
      setSuccessData({
        name: competitor.name,
        itemsCount: scrapeResult.items_count || 0
      });
      setModalState('success');
      await revalidateCompetitors();

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setModalState('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewCompetitor = async () => {
    handleClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={modalState === 'form' ? handleClose : undefined}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">

        {/* Scraping State */}
        {modalState === 'scraping' && (
          <div className="p-8 text-center">
            <div className="mx-auto w-16 h-16 bg-forkast-green-100 rounded-full flex items-center justify-center mb-6">
              <svg className="animate-spin h-8 w-8 text-forkast-green-600" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Scraping Menu Data</h2>
            <p className="text-gray-600 mb-4">{scrapingMessage}</p>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
              <div className="bg-forkast-green-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
            <p className="text-sm text-gray-500">Please wait while we fetch the menu...</p>
          </div>
        )}

        {/* Success State */}
        {modalState === 'success' && successData && (
          <div className="p-8 text-center">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
              <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Competitor Added!</h2>
            <p className="text-gray-600 mb-2">
              <span className="font-medium">{successData.name}</span> has been added.
            </p>
            {successData.itemsCount > 0 && (
              <p className="text-forkast-green-600 font-medium mb-6">
                {successData.itemsCount} menu items scraped successfully!
              </p>
            )}
            {successData.itemsCount === 0 && (
              <p className="text-gray-500 text-sm mb-6">
                No menu URL provided. Add one later to scrape menu items.
              </p>
            )}
            <button
              onClick={handleViewCompetitor}
              className="w-full px-4 py-2.5 bg-forkast-green-500 text-white text-sm font-medium rounded-lg hover:bg-forkast-green-600 transition-colors"
            >
              View Competitors
            </button>
          </div>
        )}

        {/* Error State */}
        {modalState === 'error' && (
          <div className="p-8 text-center">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-6">
              <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Something Went Wrong</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="flex gap-3">
              <button
                onClick={handleClose}
                className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => setModalState('form')}
                className="flex-1 px-4 py-2.5 bg-forkast-green-500 text-white text-sm font-medium rounded-lg hover:bg-forkast-green-600 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Form State */}
        {modalState === 'form' && (
          <>
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

              {/* Info box about scraping */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-700">
                  <strong>Tip:</strong> Add an Uber Eats URL to automatically scrape menu items and prices. Scraping takes about 1-2 minutes.
                </p>
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
                  Uber Eats URL <span className="text-forkast-green-600 text-xs">(Recommended)</span>
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
                      {scrapingMessage || 'Adding...'}
                    </>
                  ) : (
                    'Add & Scrape Menu'
                  )}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

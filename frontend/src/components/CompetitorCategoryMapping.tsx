'use client';

import CategoryMappingManager from './CategoryMappingManager';

interface CompetitorCategoryMappingProps {
  competitorId: string;
  categories: string[];
}

export default function CompetitorCategoryMapping({
  competitorId,
  categories,
}: CompetitorCategoryMappingProps) {
  if (categories.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <CategoryMappingManager
        sourceType="competitor"
        sourceId={competitorId}
        rawCategories={categories}
      />
    </div>
  );
}

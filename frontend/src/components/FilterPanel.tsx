# frontend/src/components/FilterPanel.tsx
import React from 'react';

interface FilterState {
  supplement_form: string;
  brand_name: string;
  market_status: string;
  ingredient_category: string;
}

interface FilterPanelProps {
  filters: FilterState;
  aggregations: any;
  onFilterChange: (filterType: string, value: string) => void;
  onClearFilters: () => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  aggregations,
  onFilterChange,
  onClearFilters
}) => {
  const hasActiveFilters = Object.values(filters).some(value => value !== '');

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="text-sm text-blue-500 hover:text-blue-700"
          >
            Clear All
          </button>
        )}
      </div>
      
      {/* Supplement Form Filter */}
      {aggregations?.supplement_forms && (
        <div className="mb-6">
          <h4 className="font-medium text-gray-700 mb-2">📊 Form</h4>
          <div className="space-y-2">
            {aggregations.supplement_forms.buckets.map((bucket: any) => (
              <label key={bucket.key} className="flex items-center">
                <input
                  type="radio"
                  name="supplement_form"
                  value={bucket.key}
                  checked={filters.supplement_form === bucket.key}
                  onChange={(e) => onFilterChange('supplement_form', e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-600">
                  {bucket.key.replace(/\[.*\]/, '').trim()} ({bucket.doc_count})
                </span>
              </label>
            ))}
          </div>
        </div>
      )}
      
      {/* Brand Filter */}
      {aggregations?.brands && (
        <div className="mb-6">
          <h4 className="font-medium text-gray-700 mb-2">🏢 Brand</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {aggregations.brands.buckets.slice(0, 10).map((bucket: any) => (
              <label key={bucket.key} className="flex items-center">
                <input
                  type="radio"
                  name="brand_name"
                  value={bucket.key}
                  checked={filters.brand_name === bucket.key}
                  onChange={(e) => onFilterChange('brand_name', e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-600">
                  {bucket.key} ({bucket.doc_count})
                </span>
              </label>
            ))}
          </div>
        </div>
      )}
      
      {/* Ingredient Categories */}
      {aggregations?.ingredient_categories?.categories && (
        <div className="mb-6">
          <h4 className="font-medium text-gray-700 mb-2">⚗️ Ingredient Type</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {aggregations.ingredient_categories.categories.buckets.map((bucket: any) => (
              <label key={bucket.key} className="flex items-center">
                <input
                  type="radio"
                  name="ingredient_category"
                  value={bucket.key}
                  checked={filters.ingredient_category === bucket.key}
                  onChange={(e) => onFilterChange('ingredient_category', e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-600">
                  {bucket.key} ({bucket.doc_count})
                </span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPanel;

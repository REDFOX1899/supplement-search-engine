# frontend/src/components/ProductCard.tsx
import React from 'react';

interface Ingredient {
  name: string;
  amount?: number;
  unit?: string;
  daily_value_percent?: number;
}

interface Supplement {
  dsld_id: string;
  product_name: string;
  brand_name: string;
  supplement_form: string;
  serving_size: string;
  market_status: string;
  active_ingredients: Ingredient[];
  suggested_use: string;
  score: number;
}

interface ProductCardProps {
  supplement: Supplement;
  onViewDetails: (dsld_id: string) => void;
}

const ProductCard: React.FC<ProductCardProps> = ({ supplement, onViewDetails }) => {
  const formatIngredients = (ingredients: Ingredient[]) => {
    return ingredients.slice(0, 3).map(ing => {
      const amount = ing.amount && ing.unit ? `${ing.amount} ${ing.unit}` : '';
      return `${ing.name}${amount ? ` (${amount})` : ''}`;
    }).join(', ');
  };

  const getFormIcon = (form: string) => {
    if (form.toLowerCase().includes('capsule')) return '💊';
    if (form.toLowerCase().includes('tablet')) return '🔴';
    if (form.toLowerCase().includes('gummy')) return '🟡';
    if (form.toLowerCase().includes('powder')) return '🥄';
    return '💊';
  };

  const getStatusColor = (status: string) => {
    return status === 'On Market' ? 'text-green-600' : 'text-yellow-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
          {supplement.product_name}
        </h3>
        <span className="text-2xl">{getFormIcon(supplement.supplement_form)}</span>
      </div>
      
      <div className="mb-3">
        <p className="text-sm text-gray-600">
          <span className="font-medium">Brand:</span> {supplement.brand_name || 'Not specified'}
        </p>
        <p className="text-sm text-gray-600">
          <span className="font-medium">Form:</span> {supplement.supplement_form.replace(/\[.*\]/, '').trim()}
        </p>
        <p className="text-sm text-gray-600">
          <span className="font-medium">Serving:</span> {supplement.serving_size}
        </p>
        <p className={`text-sm font-medium ${getStatusColor(supplement.market_status)}`}>
          Status: {supplement.market_status}
        </p>
      </div>
      
      {supplement.active_ingredients.length > 0 && (
        <div className="mb-3">
          <p className="text-sm font-medium text-gray-700 mb-1">Active Ingredients:</p>
          <p className="text-sm text-gray-600 line-clamp-2">
            {formatIngredients(supplement.active_ingredients)}
            {supplement.active_ingredients.length > 3 && '...'}
          </p>
        </div>
      )}
      
      {supplement.suggested_use && (
        <div className="mb-4">
          <p className="text-sm text-gray-600 line-clamp-2">
            <span className="font-medium">Use:</span> {supplement.suggested_use}
          </p>
        </div>
      )}
      
      <div className="flex justify-between items-center">
        <span className="text-xs text-gray-500">
          Relevance: {(supplement.score * 100).toFixed(0)}%
        </span>
        <button
          onClick={() => onViewDetails(supplement.dsld_id)}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
        >
          View Details
        </button>
      </div>
    </div>
  );
};

export default ProductCard;
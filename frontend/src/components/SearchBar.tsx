# frontend/src/components/SearchBar.tsx
import React, { useState, useCallback } from 'react';
import { debounce } from 'lodash';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onSuggestionSelect: (suggestion: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, onSuggestionSelect }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const fetchSuggestions = useCallback(
    debounce(async (searchQuery: string) => {
      if (searchQuery.length > 2) {
        try {
          const response = await fetch(`/api/autocomplete?q=${encodeURIComponent(searchQuery)}`);
          const data = await response.json();
          setSuggestions(data.suggestions.map((s: any) => s.text));
          setShowSuggestions(true);
        } catch (error) {
          console.error('Error fetching suggestions:', error);
        }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    }, 300),
    []
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    fetchSuggestions(value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuggestions(false);
    onSearch(query);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    onSuggestionSelect(suggestion);
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Search supplements... (e.g., 'Vitamin D3 2000 IU')"
            className="w-full px-4 py-3 pr-12 text-lg border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
          />
          <button
            type="submit"
            className="absolute right-2 top-2 p-2 text-gray-400 hover:text-blue-500"
          >
            🔍
          </button>
        </div>
        
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
              >
                {suggestion}
              </div>
            ))}
          </div>
        )}
      </form>
    </div>
  );
};

export default SearchBar;
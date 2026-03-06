import { useState, useEffect, useRef } from 'react';
import { autocompleteDrugs, lookupRxCUI, getRxNormProperties } from '../../services/rxnormApi';
import { searchPublications, getPublicationDetails } from '../../services/pubmedApi';
import type { RxNormLookupResult, Publication } from '../../types/api';
import { MedicationSafetyCard } from './MedicationSafetyCard';
import './DrugSearch.css';

interface DrugSearchProps {
  onDrugSelect?: (drugName: string, rxcui: string[]) => void;
  showPubMedSearch?: boolean;
}

export function DrugSearch({ onDrugSelect, showPubMedSearch = true }: DrugSearchProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedDrug, setSelectedDrug] = useState<string | null>(null);
  const [lookupResult, setLookupResult] = useState<RxNormLookupResult | null>(null);
  const [drugProperties, setDrugProperties] = useState<Record<string, unknown> | null>(null);
  const [pubmedResults, setPubmedResults] = useState<Publication[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<number | null>(null);
  const autocompleteCacheRef = useRef<Map<string, string[]>>(new Map());

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced autocomplete with caching
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Require at least 3 characters to reduce premature API calls
    if (searchTerm.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    // Check cache first
    const normalizedTerm = searchTerm.toLowerCase().trim();
    const cached = autocompleteCacheRef.current.get(normalizedTerm);
    if (cached) {
      setSuggestions(cached);
      setShowSuggestions(true);
      return;
    }

    // Debounce API call - increased delay to reduce requests
    debounceTimerRef.current = window.setTimeout(async () => {
      setLoading(true);
      setError(null);
      const response = await autocompleteDrugs(searchTerm);
      
      if (response.status === 'success') {
        // Cache the results
        autocompleteCacheRef.current.set(normalizedTerm, response.data);
        // Limit cache size to prevent memory issues
        if (autocompleteCacheRef.current.size > 100) {
          const firstKey = autocompleteCacheRef.current.keys().next().value;
          if (firstKey) {
            autocompleteCacheRef.current.delete(firstKey);
          }
        }
        setSuggestions(response.data);
        setShowSuggestions(true);
      } else {
        setError(response.error || 'Failed to fetch suggestions');
        setSuggestions([]);
      }
      setLoading(false);
    }, 500); // Increased from 300ms to 500ms

    return () => {
      if (debounceTimerRef.current) {
        window.clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchTerm]);

  const handleSuggestionClick = async (drugName: string) => {
    setSearchTerm(drugName);
    setSelectedDrug(drugName);
    setShowSuggestions(false);
    setError(null);
    setLoading(true);

    // Lookup RxCUI
    const lookupResponse = await lookupRxCUI(drugName);
    if (lookupResponse.status === 'success') {
      setLookupResult(lookupResponse.data);
      
      // Get properties for first RxCUI if available
      if (lookupResponse.data.rxcui.length > 0) {
        const rxcui = parseInt(lookupResponse.data.rxcui[0]);
        if (!isNaN(rxcui)) {
          const propsResponse = await getRxNormProperties(rxcui);
          if (propsResponse.status === 'success') {
            setDrugProperties(propsResponse.data);
          }
        }
      }

      // Callback
      onDrugSelect?.(drugName, lookupResponse.data.rxcui);

      // Search PubMed if enabled
      if (showPubMedSearch) {
        await searchPubMedForDrug(drugName);
      }
    } else {
      setError(lookupResponse.error || 'Failed to lookup drug');
    }
    setLoading(false);
  };

  const searchPubMedForDrug = async (drugName: string) => {
    try {
      // Extract generic drug name for better PubMed search results
      // Remove dosage, form, and brand name info (e.g., "isotretinoin 10 MG Oral Capsule [Accutane]" -> "isotretinoin")
      let normalizedName = drugName;
      
      // Extract name before brackets (brand name)
      const bracketIndex = normalizedName.indexOf('[');
      if (bracketIndex > 0) {
        normalizedName = normalizedName.substring(0, bracketIndex).trim();
      }
      
      // Remove dosage and form info (numbers, units like MG, forms like Capsule, Tablet, etc.)
      // Keep only the first word or two (usually the generic name)
      const words = normalizedName.split(/\s+/);
      const genericName = words[0]; // First word is usually the generic drug name
      
      // Use generic name for PubMed search
      const query = `${genericName} pregnancy safety`;
      const searchResponse = await searchPublications(query, 0, 5);
      
      if (searchResponse.status === 'success' && searchResponse.data.ids.length > 0) {
        const detailsResponse = await getPublicationDetails(searchResponse.data.ids, 'all');
        if (detailsResponse.status === 'success') {
          setPubmedResults(detailsResponse.data.results);
        }
      }
    } catch (err) {
      console.error('PubMed search error:', err);
    }
  };

  const handleClear = () => {
    setSearchTerm('');
    setSelectedDrug(null);
    setLookupResult(null);
    setDrugProperties(null);
    setPubmedResults([]);
    setError(null);
    setSuggestions([]);
  };

  return (
    <div className="drug-search" ref={searchRef}>
      <div className="drug-search-header">
        <h3>Drug Search</h3>
        {selectedDrug && (
          <button className="clear-button" onClick={handleClear} type="button">
            Clear
          </button>
        )}
      </div>

      <div className="drug-search-input-container">
        <input
          type="text"
          className="drug-search-input"
          placeholder="Type drug name (e.g., isotretinoin, acetaminophen)..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setSelectedDrug(null);
            setLookupResult(null);
            setDrugProperties(null);
            setPubmedResults([]);
          }}
        />
        {loading && <div className="loading-spinner" />}
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="suggestions-dropdown">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="suggestion-item"
              onClick={() => handleSuggestionClick(suggestion)}
              type="button"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Selected Drug Information */}
      {selectedDrug && lookupResult && (
        <div className="drug-info">
          {/* Medication Safety Card */}
          <MedicationSafetyCard
            medication={{
              drugName: selectedDrug,
              rxcui: lookupResult.rxcui,
              properties: drugProperties || undefined,
              pubmedResults: pubmedResults.length > 0 ? pubmedResults : undefined,
            }}
          />
        </div>
      )}
    </div>
  );
}


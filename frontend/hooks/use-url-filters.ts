/**
 * Custom hook for managing search filters in URL params
 * Enables shareable search URLs with filter state
 */

import { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { SearchFilters } from '@/lib/types/search-history';

export function useUrlFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [filters, setFiltersState] = useState<SearchFilters>({});

  // Parse filters from URL on mount and when URL changes
  useEffect(() => {
    const parsedFilters: SearchFilters = {};

    // Parse sources
    const sources = searchParams.get('sources');
    if (sources) {
      parsedFilters.sources = sources.split(',') as ('pubmed' | 'clinical_trials' | 'fda')[];
    }

    // Parse year range
    const yearStart = searchParams.get('year_start');
    const yearEnd = searchParams.get('year_end');
    if (yearStart || yearEnd) {
      parsedFilters.year_range = {
        start: yearStart ? parseInt(yearStart, 10) : undefined,
        end: yearEnd ? parseInt(yearEnd, 10) : undefined,
      };
    }

    // Parse study types
    const studyTypes = searchParams.get('study_types');
    if (studyTypes) {
      parsedFilters.study_types = studyTypes.split(',');
    }

    // Parse min confidence
    const minConfidence = searchParams.get('min_confidence');
    if (minConfidence) {
      parsedFilters.minConfidence = parseInt(minConfidence, 10);
    }

    // Parse sort by
    const sortBy = searchParams.get('sort_by');
    if (sortBy) {
      parsedFilters.sortBy = sortBy as 'date' | 'relevance' | 'confidence';
    }

    setFiltersState(parsedFilters);
  }, [searchParams]);

  // Update URL when filters change
  const setFilters = useCallback(
    (newFilters: SearchFilters) => {
      setFiltersState(newFilters);

      // Build URL params
      const params = new URLSearchParams();

      if (newFilters.sources && newFilters.sources.length > 0) {
        params.set('sources', newFilters.sources.join(','));
      }

      if (newFilters.year_range) {
        if (newFilters.year_range.start) {
          params.set('year_start', newFilters.year_range.start.toString());
        }
        if (newFilters.year_range.end) {
          params.set('year_range.end', newFilters.year_range.end.toString());
        }
      }

      if (newFilters.study_types && newFilters.study_types.length > 0) {
        params.set('study_types', newFilters.study_types.join(','));
      }

      if (newFilters.minConfidence !== undefined) {
        params.set('min_confidence', newFilters.minConfidence.toString());
      }

      if (newFilters.sortBy) {
        params.set('sort_by', newFilters.sortBy);
      }

      // Update URL without page reload
      const newUrl = params.toString() ? `?${params.toString()}` : '/';
      router.replace(newUrl, { scroll: false });
    },
    [router]
  );

  // Get shareable URL
  const getShareableUrl = useCallback(() => {
    if (typeof window === 'undefined') return '';
    return window.location.href;
  }, []);

  return {
    filters,
    setFilters,
    getShareableUrl,
  };
}


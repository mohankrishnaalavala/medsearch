"use client";

import { useState } from "react";
import { SlidersHorizontal, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { SearchFilters } from "@/lib/types/search-history";

interface SearchFiltersProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
}

const QUICK_FILTERS = [
  { label: "Recent (Last 2 years)", value: "recent" },
  { label: "High Confidence (>90%)", value: "high_confidence" },
  { label: "Clinical Trials Only", value: "clinical_trials" },
  { label: "FDA Approved", value: "fda_approved" },
];

const SOURCES = [
  { label: "PubMed", value: "pubmed" as const },
  { label: "Clinical Trials", value: "clinical_trials" as const },
  { label: "FDA", value: "fda" as const },
];

export function SearchFiltersComponent({ filters, onFiltersChange }: SearchFiltersProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleSourceToggle = (source: "pubmed" | "clinical_trials" | "fda") => {
    const currentSources = filters.sources || [];
    const newSources = currentSources.includes(source)
      ? currentSources.filter((s) => s !== source)
      : [...currentSources, source];

    onFiltersChange({
      ...filters,
      sources: newSources.length > 0 ? newSources : undefined,
    });
  };

  const handleConfidenceChange = (value: number[]) => {
    onFiltersChange({
      ...filters,
      minConfidence: value[0],
    });
  };

  const handleSortChange = (value: string) => {
    onFiltersChange({
      ...filters,
      sortBy: value as "date" | "relevance" | "confidence",
    });
  };

  const handleQuickFilter = (filterType: string) => {
    switch (filterType) {
      case "recent":
        const twoYearsAgo = new Date();
        twoYearsAgo.setFullYear(twoYearsAgo.getFullYear() - 2);
        onFiltersChange({
          ...filters,
          dateRange: { start: twoYearsAgo, end: new Date() },
        });
        break;
      case "high_confidence":
        onFiltersChange({
          ...filters,
          minConfidence: 90,
        });
        break;
      case "clinical_trials":
        onFiltersChange({
          ...filters,
          sources: ["clinical_trials"],
        });
        break;
      case "fda_approved":
        onFiltersChange({
          ...filters,
          sources: ["fda"],
        });
        break;
    }
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  const activeFiltersCount =
    (filters.sources?.length || 0) +
    (filters.minConfidence ? 1 : 0) +
    (filters.dateRange ? 1 : 0) +
    (filters.sortBy ? 1 : 0);

  return (
    <div className="flex items-center gap-2">
      {/* Quick Filters */}
      <div className="hidden md:flex items-center gap-2">
        {QUICK_FILTERS.map((filter) => (
          <Button
            key={filter.value}
            variant="outline"
            size="sm"
            onClick={() => handleQuickFilter(filter.value)}
            className="text-xs"
          >
            {filter.label}
          </Button>
        ))}
      </div>

      {/* Advanced Filters Popover */}
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <SlidersHorizontal className="h-4 w-4" />
            Filters
            {activeFiltersCount > 0 && (
              <Badge variant="secondary" className="ml-1 h-5 w-5 rounded-full p-0 flex items-center justify-center">
                {activeFiltersCount}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-sm">Advanced Filters</h4>
              {activeFiltersCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="h-auto p-1 text-xs"
                >
                  Clear all
                </Button>
              )}
            </div>

            {/* Data Sources */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Data Sources</Label>
              <div className="space-y-2">
                {SOURCES.map((source) => (
                  <div key={source.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={source.value}
                      checked={filters.sources?.includes(source.value)}
                      onCheckedChange={() => handleSourceToggle(source.value)}
                    />
                    <label
                      htmlFor={source.value}
                      className="text-sm font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      {source.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Confidence Threshold */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">
                Minimum Confidence: {filters.minConfidence || 0}%
              </Label>
              <Slider
                value={[filters.minConfidence || 0]}
                onValueChange={handleConfidenceChange}
                max={100}
                step={5}
                className="w-full"
              />
            </div>

            {/* Sort By */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Sort By</Label>
              <Select value={filters.sortBy || "relevance"} onValueChange={handleSortChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select sort order" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="relevance">Relevance</SelectItem>
                  <SelectItem value="date">Publication Date</SelectItem>
                  <SelectItem value="confidence">Confidence Score</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Active Filters Display */}
      {activeFiltersCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={clearFilters}
          className="gap-1 text-xs"
        >
          <X className="h-3 w-3" />
          Clear
        </Button>
      )}
    </div>
  );
}


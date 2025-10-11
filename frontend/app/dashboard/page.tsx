"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { TrendingUp, Clock, Star, Activity, Search } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SearchHistoryCard } from "@/components/search-history-card";
import { SearchFiltersComponent } from "@/components/search-filters";
import { Button } from "@/components/ui/button";
import {
  getSearchHistory,
  getSavedSearches,
  toggleSavedSearch,
  deleteSearchHistoryItem,
} from "@/lib/utils/search-history";
import { SearchHistoryItem, SearchFilters } from "@/lib/types/search-history";

export default function DashboardPage() {
  const router = useRouter();
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [savedSearches, setSavedSearches] = useState<SearchHistoryItem[]>([]);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [activeTab, setActiveTab] = useState("recent");

  useEffect(() => {
    loadSearchHistory();
  }, []);

  const loadSearchHistory = () => {
    setSearchHistory(getSearchHistory());
    setSavedSearches(getSavedSearches());
  };

  const handleRerunSearch = (query: string) => {
    // Navigate to home page with query
    router.push(`/?q=${encodeURIComponent(query)}`);
  };

  const handleToggleSave = (searchId: string) => {
    toggleSavedSearch(searchId);
    loadSearchHistory();
  };

  const handleDelete = (searchId: string) => {
    deleteSearchHistoryItem(searchId);
    loadSearchHistory();
  };

  const applyFilters = (items: SearchHistoryItem[]): SearchHistoryItem[] => {
    let filtered = [...items];

    // Filter by sources
    if (filters.sources && filters.sources.length > 0) {
      filtered = filtered.filter((item) =>
        item.sources.some((source) => {
          const lowerSource = source.toLowerCase();
          return filters.sources?.includes(lowerSource as 'pubmed' | 'clinical_trials' | 'fda');
        })
      );
    }

    // Filter by confidence
    if (filters.minConfidence) {
      filtered = filtered.filter(
        (item) => item.avgConfidence >= filters.minConfidence!
      );
    }

    // Filter by date range
    if (filters.dateRange) {
      filtered = filtered.filter((item) => {
        const itemDate = new Date(item.timestamp);
        return (
          itemDate >= filters.dateRange!.start &&
          itemDate <= filters.dateRange!.end
        );
      });
    }

    // Sort
    if (filters.sortBy) {
      filtered.sort((a, b) => {
        switch (filters.sortBy) {
          case "date":
            return b.timestamp.getTime() - a.timestamp.getTime();
          case "confidence":
            return b.avgConfidence - a.avgConfidence;
          case "relevance":
          default:
            return b.resultsCount - a.resultsCount;
        }
      });
    }

    return filtered;
  };

  const filteredHistory = applyFilters(searchHistory);
  const filteredSaved = applyFilters(savedSearches);

  const stats = {
    totalSearches: searchHistory.length,
    savedSearches: savedSearches.length,
    avgConfidence:
      searchHistory.length > 0
        ? Math.round(
            searchHistory.reduce((sum, item) => sum + item.avgConfidence, 0) /
              searchHistory.length
          )
        : 0,
    totalResults: searchHistory.reduce(
      (sum, item) => sum + item.resultsCount,
      0
    ),
  };

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
              <p className="text-sm text-muted-foreground mt-1">
                View and manage your search history
              </p>
            </div>
            <Button onClick={() => router.push("/")} className="gap-2">
              <Search className="h-4 w-4" />
              New Search
            </Button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Activity className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Total Searches</p>
                  <p className="text-2xl font-bold">{stats.totalSearches}</p>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-accent/10">
                  <Star className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Saved</p>
                  <p className="text-2xl font-bold">{stats.savedSearches}</p>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-500/10">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Avg Confidence</p>
                  <p className="text-2xl font-bold">{stats.avgConfidence}%</p>
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <Clock className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Total Results</p>
                  <p className="text-2xl font-bold">{stats.totalResults}</p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        <div className="container mx-auto px-4 py-6 h-full">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <TabsList>
                <TabsTrigger value="recent">
                  Recent Searches ({filteredHistory.length})
                </TabsTrigger>
                <TabsTrigger value="saved">
                  Saved ({filteredSaved.length})
                </TabsTrigger>
              </TabsList>

              <SearchFiltersComponent
                filters={filters}
                onFiltersChange={setFilters}
              />
            </div>

            <TabsContent value="recent" className="flex-1 mt-0">
              <ScrollArea className="h-[calc(100vh-20rem)]">
                {filteredHistory.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-4">
                    {filteredHistory.map((search) => (
                      <SearchHistoryCard
                        key={search.id}
                        search={search}
                        onRerun={handleRerunSearch}
                        onToggleSave={handleToggleSave}
                        onDelete={handleDelete}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <Clock className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">
                      No search history
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Your recent searches will appear here
                    </p>
                    <Button onClick={() => router.push("/")} variant="outline">
                      Start Searching
                    </Button>
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="saved" className="flex-1 mt-0">
              <ScrollArea className="h-[calc(100vh-20rem)]">
                {filteredSaved.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-4">
                    {filteredSaved.map((search) => (
                      <SearchHistoryCard
                        key={search.id}
                        search={search}
                        onRerun={handleRerunSearch}
                        onToggleSave={handleToggleSave}
                        onDelete={handleDelete}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <Star className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium text-foreground mb-2">
                      No saved searches
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Save your favorite searches for quick access
                    </p>
                    <Button onClick={() => setActiveTab("recent")} variant="outline">
                      View Recent Searches
                    </Button>
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}


"use client";

import { Clock, FileText, TrendingUp, Star, MoreVertical, Repeat } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SearchHistoryItem } from "@/lib/types/search-history";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface SearchHistoryCardProps {
  search: SearchHistoryItem;
  onRerun?: (query: string) => void;
  onToggleSave?: (id: string) => void;
  onDelete?: (id: string) => void;
}

const sourceColors: Record<string, string> = {
  PubMed: "bg-primary/10 text-primary border-primary/20",
  "Clinical Trials": "bg-accent/10 text-accent border-accent/20",
  FDA: "bg-warning/10 text-warning border-warning/20",
  pubmed: "bg-primary/10 text-primary border-primary/20",
  clinical_trials: "bg-accent/10 text-accent border-accent/20",
  fda: "bg-warning/10 text-warning border-warning/20",
};

export function SearchHistoryCard({
  search,
  onRerun,
  onToggleSave,
  onDelete,
}: SearchHistoryCardProps) {
  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays === 1) return "1 day ago";
    return `${diffDays} days ago`;
  };

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="text-sm font-medium text-foreground leading-tight line-clamp-2">
              {search.query}
            </h3>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0 -mt-1">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onRerun?.(search.query)}>
                  <Repeat className="h-4 w-4 mr-2" />
                  Re-run Search
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onToggleSave?.(search.id)}>
                  <Star className="h-4 w-4 mr-2" />
                  {search.isSaved ? "Unsave" : "Save"}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => onDelete?.(search.id)}
                  className="text-destructive"
                >
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
            <Clock className="h-3 w-3" />
            <span>{formatTimestamp(search.timestamp)}</span>
          </div>

          <div className="flex flex-wrap items-center gap-2 mb-3">
            {search.sources.map((source) => (
              <Badge
                key={source}
                variant="outline"
                className={sourceColors[source] || ""}
              >
                {source}
              </Badge>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <FileText className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">
                  {search.resultsCount} results
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <TrendingUp className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">
                  {search.avgConfidence}% confidence
                </span>
              </div>
            </div>

            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => onToggleSave?.(search.id)}
              >
                <Star
                  className={`h-3 w-3 ${
                    search.isSaved ? "fill-primary text-primary" : ""
                  }`}
                />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => onRerun?.(search.query)}
              >
                <Repeat className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}


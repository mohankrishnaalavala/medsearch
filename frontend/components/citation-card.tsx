'use client';

import { Citation } from '@/lib/types';
import { cn } from '@/lib/utils';
import { ExternalLink, FileText, Beaker, Pill } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface CitationCardProps {
  citation: Citation;
  index?: number;
  expanded?: boolean;
  onToggle?: () => void;
}

export function CitationCard({ citation, index, expanded = false, onToggle }: CitationCardProps) {
  const getSourceIcon = () => {
    switch (citation.source_type) {
      case 'pubmed':
        return <FileText className="w-4 h-4" />;
      case 'clinical_trial':
        return <Beaker className="w-4 h-4" />;
      case 'drug_info':
        return <Pill className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getSourceLabel = () => {
    switch (citation.source_type) {
      case 'pubmed':
        return 'PubMed';
      case 'clinical_trial':
        return 'Clinical Trial';
      case 'drug_info':
        return 'Drug Information';
      default:
        return 'Unknown';
    }
  };

  const getSourceColor = () => {
    switch (citation.source_type) {
      case 'pubmed':
        return 'bg-blue-500/10 text-blue-700 dark:text-blue-300';
      case 'clinical_trial':
        return 'bg-green-500/10 text-green-700 dark:text-green-300';
      case 'drug_info':
        return 'bg-purple-500/10 text-purple-700 dark:text-purple-300';
      default:
        return 'bg-gray-500/10 text-gray-700 dark:text-gray-300';
    }
  };

  return (
    <Card
      className={cn(
        'transition-all duration-200',
        expanded ? 'shadow-md' : 'shadow-sm hover:shadow-md',
        onToggle && 'cursor-pointer'
      )}
      onClick={onToggle}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            {index !== undefined && (
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-mono flex items-center justify-center">
                {index}
              </span>
            )}
            <Badge variant="outline" className={cn('gap-1', getSourceColor())}>
              {getSourceIcon()}
              {getSourceLabel()}
            </Badge>
          </div>
          <Badge variant="secondary" className="text-xs">
            {Math.round(citation.relevance_score * 100)}% match
          </Badge>
        </div>
        <CardTitle className="text-base mt-2 line-clamp-2">
          {citation.title}
        </CardTitle>
        {citation.authors && citation.authors.length > 0 && (
          <CardDescription className="text-xs">
            {citation.authors.slice(0, 3).join(', ')}
            {citation.authors.length > 3 && ` et al.`}
          </CardDescription>
        )}
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0">
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground line-clamp-3">
              {citation.snippet}
            </p>

            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              {citation.journal && (
                <span className="flex items-center gap-1">
                  <FileText className="w-3 h-3" />
                  {citation.journal}
                </span>
              )}
              {citation.publication_date && (
                <span>• {citation.publication_date}</span>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {citation.pmid && (
                <Badge variant="outline" className="text-xs">
                  PMID: {citation.pmid}
                </Badge>
              )}
              {citation.nct_id && (
                <Badge variant="outline" className="text-xs">
                  NCT: {citation.nct_id}
                </Badge>
              )}
              {citation.doi && (
                <Badge variant="outline" className="text-xs">
                  DOI: {citation.doi}
                </Badge>
              )}
            </div>

            {citation.url && (
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                View source
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}


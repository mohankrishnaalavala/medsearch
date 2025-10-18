'use client';

import { Citation } from '@/lib/types';
import { cn } from '@/lib/utils';
import { ExternalLink, FileText, Beaker, Pill, Calendar, FlaskConical, Copy, Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useState } from 'react';

interface CitationCardProps {
  citation: Citation;
  index?: number;
  expanded?: boolean;
  onToggle?: () => void;
}

export function CitationCard({ citation, index, expanded = false, onToggle }: CitationCardProps) {
  const [copied, setCopied] = useState(false);

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
        return 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
      case 'clinical_trial':
        return 'bg-green-500/10 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800';
      case 'drug_info':
        return 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800';
      default:
        return 'bg-gray-500/10 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-800';
    }
  };

  const getYear = () => {
    if (!citation.publication_date) return null;
    try {
      return new Date(citation.publication_date).getFullYear();
    } catch {
      return null;
    }
  };

  const getStudyType = () => {
    // Infer study type from source
    if (citation.source_type === 'clinical_trial') {
      return 'Clinical Trial';
    }
    if (citation.source_type === 'pubmed') {
      // Could be enhanced to detect from title/abstract
      return 'Research Article';
    }
    if (citation.source_type === 'drug_info') {
      return 'Drug Info';
    }
    return null;
  };

  const copyCitation = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const citationText = `${citation.title}. ${citation.authors?.join(', ') || ''}. ${citation.journal || ''}. ${citation.publication_date || ''}. ${citation.doi ? `DOI: ${citation.doi}` : ''}`;
    await navigator.clipboard.writeText(citationText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const year = getYear();
  const studyType = getStudyType();

  return (
    <TooltipProvider>
      <Tooltip delayDuration={300}>
        <TooltipTrigger asChild>
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
                <div className="flex items-center gap-2 flex-wrap">
                  {index !== undefined && (
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-mono flex items-center justify-center">
                      {index}
                    </span>
                  )}
                  <Badge variant="outline" className={cn('gap-1', getSourceColor())}>
                    {getSourceIcon()}
                    {getSourceLabel()}
                  </Badge>
                  {year && (
                    <Badge variant="outline" className="gap-1 text-xs">
                      <Calendar className="w-3 h-3" />
                      {year}
                    </Badge>
                  )}
                  {studyType && (
                    <Badge variant="outline" className="gap-1 text-xs">
                      <FlaskConical className="w-3 h-3" />
                      {studyType}
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Badge variant="secondary" className="text-xs">
                    {Math.round(citation.relevance_score * 100)}%
                  </Badge>
                  <button
                    onClick={copyCitation}
                    className="p-1 hover:bg-muted rounded transition-colors"
                    aria-label="Copy citation"
                  >
                    {copied ? (
                      <Check className="w-3 h-3 text-green-600" />
                    ) : (
                      <Copy className="w-3 h-3 text-muted-foreground" />
                    )}
                  </button>
                </div>
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
        </TooltipTrigger>
        <TooltipContent side="left" className="max-w-sm">
          <div className="space-y-2">
            <p className="font-semibold text-sm">{citation.title}</p>
            <p className="text-xs text-muted-foreground line-clamp-3">
              {citation.snippet}
            </p>
            {citation.authors && citation.authors.length > 0 && (
              <p className="text-xs">
                <span className="font-medium">Authors:</span> {citation.authors.slice(0, 2).join(', ')}
                {citation.authors.length > 2 && ' et al.'}
              </p>
            )}
            {citation.journal && (
              <p className="text-xs">
                <span className="font-medium">Journal:</span> {citation.journal}
              </p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}


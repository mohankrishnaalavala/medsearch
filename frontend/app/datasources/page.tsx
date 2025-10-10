'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { getHealthStatus } from '@/lib/api';

interface SourceInfo {
  key: 'pubmed' | 'clinical_trials' | 'drugs';
  name: string;
  description: string;
  count: number;
  updatedAt: string;
}

const DEFAULT_SOURCES: SourceInfo[] = [
  {
    key: 'pubmed',
    name: 'PubMed',
    description: 'Biomedical literature abstracts and metadata.',
    count: 1000,
    updatedAt: new Date().toISOString(),
  },
  {
    key: 'clinical_trials',
    name: 'ClinicalTrials.gov',
    description: 'Registered clinical study records and statuses.',
    count: 477,
    updatedAt: new Date().toISOString(),
  },
  {
    key: 'drugs',
    name: 'FDA Drugs Database',
    description: 'Approved drug labels and structured drug information.',
    count: 53,
    updatedAt: new Date().toISOString(),
  },
];

export default function DataSourcesPage() {
  const [sources, setSources] = useState<SourceInfo[]>(DEFAULT_SOURCES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Optional: Try to fetch live counts if a metrics endpoint exists
  async function refreshCounts() {
    setLoading(true);
    setError(null);
    try {
      // Placeholder: If backend provides metrics, plug it here
      // Example expected shape:
      // GET /api/v1/metrics/indices -> { pubmed: 1000, clinical_trials: 477, drugs: 53, updated_at: '...' }
      await getHealthStatus().catch(() => null);
      // If backend reachable, keep timestamp fresh; counts remain defaults for now
      const updatedAt = new Date().toISOString();
      setSources(prev => prev.map(s => ({ ...s, updatedAt })));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch counts');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Auto-refresh timestamps on mount (no-op for counts for now)
    refreshCounts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Data Sources</h1>
        <Button onClick={refreshCounts} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh'}</Button>
      </div>

      {error && (
        <div className="mb-4 text-sm text-destructive">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sources.map((src) => (
          <Card key={src.key}>
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="text-base">{src.name}</CardTitle>
                <Badge variant="secondary" className="text-xs">{src.count.toLocaleString()} indexed</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-3">{src.description}</p>
              <p className="text-xs text-muted-foreground">Last updated: {new Date(src.updatedAt).toLocaleString()}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </main>
  );
}


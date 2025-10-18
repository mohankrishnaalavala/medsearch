/**
 * Skeleton UI for loading messages
 * Provides visual feedback while waiting for AI response
 */

import { Skeleton } from '@/components/ui/skeleton';
import { Card } from '@/components/ui/card';

export function MessageSkeleton() {
  return (
    <div className="flex gap-3 max-w-4xl mx-auto px-4 py-4">
      <div className="flex-shrink-0">
        <Skeleton className="h-8 w-8 rounded-full" />
      </div>
      <div className="flex-1 space-y-3">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <div className="pt-2 space-y-2">
          <Skeleton className="h-20 w-full rounded-lg" />
          <Skeleton className="h-20 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function CitationSkeleton() {
  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Skeleton className="h-6 w-6 rounded-full" />
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-5 w-16 ml-auto" />
      </div>
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-4/5" />
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-6 w-20" />
        <Skeleton className="h-6 w-20" />
      </div>
    </Card>
  );
}

export function AgentStatusSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="space-y-2">
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-16" />
          </div>
          <Skeleton className="h-2 w-full rounded-full" />
        </div>
      ))}
    </div>
  );
}


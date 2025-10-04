'use client';

import { AgentStatus as AgentStatusType } from '@/lib/types';
import { cn } from '@/lib/utils';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface AgentStatusProps {
  agents: AgentStatusType[];
}

export function AgentStatus({ agents }: AgentStatusProps) {
  if (agents.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3 p-4 bg-muted/50 rounded-lg border border-border">
      <h3 className="text-sm font-medium flex items-center gap-2">
        <Loader2 className="w-4 h-4 animate-spin" />
        Processing your search...
      </h3>

      <div className="space-y-2">
        {agents.map((agent) => (
          <AgentStatusItem key={agent.name} agent={agent} />
        ))}
      </div>
    </div>
  );
}

interface AgentStatusItemProps {
  agent: AgentStatusType;
}

function AgentStatusItem({ agent }: AgentStatusItemProps) {
  const getStatusIcon = () => {
    switch (agent.status) {
      case 'idle':
        return <Circle className="w-4 h-4 text-muted-foreground" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-primary animate-spin" />;
      case 'complete':
        return <CheckCircle2 className="w-4 h-4 text-green-600" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-destructive" />;
      default:
        return <Circle className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = () => {
    switch (agent.status) {
      case 'running':
        return 'text-primary';
      case 'complete':
        return 'text-green-600';
      case 'error':
        return 'text-destructive';
      default:
        return 'text-muted-foreground';
    }
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {getStatusIcon()}
          <span className={cn('text-sm font-medium truncate', getStatusColor())}>
            {agent.name}
          </span>
        </div>
        {agent.execution_time !== undefined && (
          <span className="text-xs text-muted-foreground flex-shrink-0">
            {agent.execution_time.toFixed(1)}s
          </span>
        )}
      </div>

      {agent.status === 'running' && (
        <div className="space-y-1 pl-6">
          <Progress value={agent.progress} className="h-1" />
          <p className="text-xs text-muted-foreground">{agent.message}</p>
        </div>
      )}

      {agent.status === 'error' && (
        <p className="text-xs text-destructive pl-6">{agent.message}</p>
      )}
    </div>
  );
}


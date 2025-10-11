'use client';

import { ChatInterface } from '@/components/chat-interface';
import { ProtectedRoute } from '@/components/protected-route';

export default function Home() {
  return (
    <ProtectedRoute>
      <div className="relative h-full">
        <ChatInterface />
      </div>
    </ProtectedRoute>
  );
}


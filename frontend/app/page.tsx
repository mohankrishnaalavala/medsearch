'use client';

import { ChatInterface } from '@/components/chat-interface';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);

  useEffect(() => {
    // Check if user is logged in
    const userData = localStorage.getItem('medsearch_user');
    if (userData) {
      try {
        const parsed = JSON.parse(userData);
        if (parsed.loggedIn) {
          setUser({ name: parsed.name, email: parsed.email });
        } else {
          router.push('/login');
        }
      } catch (error) {
        console.error('Failed to parse user data:', error);
        router.push('/login');
      }
    } else {
      router.push('/login');
    }
  }, [router]);

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-full">
      <ChatInterface />
    </div>
  );
}


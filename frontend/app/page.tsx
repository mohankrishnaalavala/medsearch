'use client';

import { ChatInterface } from '@/components/chat-interface';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { LogOut, User } from 'lucide-react';

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

  const handleLogout = () => {
    localStorage.removeItem('medsearch_user');
    router.push('/login');
  };

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
    <div className="relative h-screen">
      {/* Header with user info and logout */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background/80 backdrop-blur-sm border border-border/50">
          <User className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">{user.name}</span>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleLogout}
          className="gap-2"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>

      <ChatInterface />
    </div>
  );
}


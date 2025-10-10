'use client';

import { useEffect, useState } from 'react';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

export default function SettingsPage() {
  const [theme, setTheme] = useState<'system' | 'light' | 'dark'>('system');
  const [compact, setCompact] = useState<boolean>(false);

  useEffect(() => {
    const savedTheme = (localStorage.getItem('medsearch_theme') as 'system' | 'light' | 'dark') || 'system';
    const savedCompact = localStorage.getItem('medsearch_compact') === '1';
    setTheme(savedTheme);
    setCompact(savedCompact);
  }, []);

  useEffect(() => {
    localStorage.setItem('medsearch_theme', theme);
    const root = document.documentElement;
    if (theme === 'dark') root.classList.add('dark');
    else if (theme === 'light') root.classList.remove('dark');
    else {
      // system: rely on prefers-color-scheme; do nothing explicit
    }
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('medsearch_compact', compact ? '1' : '0');
    document.body.dataset.compact = compact ? '1' : '0';
  }, [compact]);

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <section className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="theme">Theme</Label>
          <div id="theme" className="flex gap-2">
            <Button variant={theme==='system' ? 'default' : 'outline'} onClick={() => setTheme('system')}>System</Button>
            <Button variant={theme==='light' ? 'default' : 'outline'} onClick={() => setTheme('light')}>Light</Button>
            <Button variant={theme==='dark' ? 'default' : 'outline'} onClick={() => setTheme('dark')}>Dark</Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="compact">Display density</Label>
          <div className="flex items-center gap-3">
            <input
              id="compact"
              type="checkbox"
              checked={compact}
              onChange={(e) => setCompact(e.target.checked)}
              className="h-4 w-4"
            />
            <span className="text-sm text-muted-foreground">Compact mode</span>
          </div>
        </div>
      </section>
    </main>
  );
}


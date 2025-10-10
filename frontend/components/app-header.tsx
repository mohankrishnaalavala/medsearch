"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FC } from "react";

const HIDE_ON: readonly string[] = ["/login", "/signup"]; // hide header on auth pages

export const AppHeader: FC = () => {
  const pathname = usePathname();
  if (HIDE_ON.some((p) => pathname?.startsWith(p))) return null;

  return (
    <header className="border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="font-semibold">MedSearch AI</Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/" className="text-muted-foreground hover:text-foreground">Dashboard</Link>
          <Link href="/" className="text-muted-foreground hover:text-foreground">Search</Link>
          <Link href="/citations" className="text-muted-foreground hover:text-foreground">Citations</Link>
          <Link href="/settings" className="text-muted-foreground hover:text-foreground">Settings</Link>
        </nav>
      </div>
    </header>
  );
};


"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FC } from "react";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";

const HIDE_ON: readonly string[] = ["/login", "/signup"]; // hide header on auth pages

export const AppHeader: FC = () => {
  const pathname = usePathname();
  const { theme, toggleTheme, mounted } = useTheme();

  if (HIDE_ON.some((p) => pathname?.startsWith(p))) return null;

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="font-semibold text-lg">MedSearch AI</Link>
        <nav className="flex items-center gap-6 text-sm font-medium">
          <Link
            href="/dashboard"
            className={pathname === "/dashboard" ? "text-foreground" : "text-muted-foreground hover:text-foreground transition-colors"}
          >
            Dashboard
          </Link>
          <Link
            href="/"
            className={pathname === "/" ? "text-foreground" : "text-muted-foreground hover:text-foreground transition-colors"}
          >
            Search
          </Link>
          <Link
            href="/citations"
            className={pathname === "/citations" ? "text-foreground" : "text-muted-foreground hover:text-foreground transition-colors"}
          >
            Citations
          </Link>
          <Link
            href="/datasources"
            className={pathname === "/datasources" ? "text-foreground" : "text-muted-foreground hover:text-foreground transition-colors"}
          >
            Data Sources
          </Link>
          <Link
            href="/settings"
            className={pathname === "/settings" ? "text-foreground" : "text-muted-foreground hover:text-foreground transition-colors"}
          >
            Settings
          </Link>
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
              className="h-9 w-9"
            >
              {theme === "light" ? (
                <Moon className="h-4 w-4" />
              ) : (
                <Sun className="h-4 w-4" />
              )}
            </Button>
          )}
        </nav>
      </div>
    </header>
  );
};


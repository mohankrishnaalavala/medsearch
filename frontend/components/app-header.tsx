"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FC } from "react";
import { Moon, Sun, LogOut, User, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/contexts/auth-context";
import { useToast } from "@/hooks/use-toast";

const HIDE_ON: readonly string[] = ["/login", "/signup"]; // hide header on auth pages

export const AppHeader: FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const { toast } = useToast();
  const { theme, toggleTheme, mounted } = useTheme();
  const { user, logout } = useAuth();

  if (HIDE_ON.some((p) => pathname?.startsWith(p))) return null;

  const handleLogout = () => {
    logout();
    toast({
      title: "Logged out successfully",
      description: "You have been logged out of your account",
    });
    router.push("/login");
  };

  const getUserInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-semibold text-lg">
          <Activity className="h-6 w-6 text-primary" />
          <span>MedSearch AI</span>
        </Link>
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
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                  <Avatar className="h-9 w-9">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      {getUserInitials(user.name)}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{user.name}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => router.push("/settings")}>
                  <User className="mr-2 h-4 w-4" />
                  <span>Profile Settings</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600 dark:text-red-400">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </nav>
      </div>
    </header>
  );
};


import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MedSearch AI - Medical Research Assistant",
  description: "Multi-agent medical research assistant powered by AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <header className="border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
            <Link href="/" className="font-semibold">MedSearch AI</Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link href="/datasources" className="text-muted-foreground hover:text-foreground">Data Sources</Link>
              <Link href="/settings" className="text-muted-foreground hover:text-foreground">Settings</Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}


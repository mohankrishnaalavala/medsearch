import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppHeader } from "@/components/app-header";

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
        <AppHeader />
        {children}
      </body>
    </html>
  );
}


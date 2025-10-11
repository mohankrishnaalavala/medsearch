"use client";

import { useState } from "react";
import { Download, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Citation } from "@/lib/types/index";
import {
  exportCitations,
  exportToBibTeX,
  copyToClipboard,
} from "@/lib/utils/citation-export";
import { useToast } from "@/hooks/use-toast";

interface CitationExportProps {
  citations: Citation[];
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
}

export function CitationExport({
  citations,
  variant = "outline",
  size = "sm",
}: CitationExportProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleExport = (format: "bibtex" | "ris" | "csv" | "json") => {
    try {
      exportCitations(citations, format);
      toast({
        title: "Export Successful",
        description: `Exported ${citations.length} citation${
          citations.length !== 1 ? "s" : ""
        } to ${format.toUpperCase()}`,
      });
    } catch (error) {
      console.error("Export failed:", error);
      toast({
        title: "Export Failed",
        description: "Failed to export citations. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleCopyBibTeX = async () => {
    try {
      const bibtex = exportToBibTeX(citations);
      const success = await copyToClipboard(bibtex);

      if (success) {
        setCopied(true);
        toast({
          title: "Copied to Clipboard",
          description: `Copied ${citations.length} citation${
            citations.length !== 1 ? "s" : ""
          } in BibTeX format`,
        });
        setTimeout(() => setCopied(false), 2000);
      } else {
        throw new Error("Clipboard API failed");
      }
    } catch (error) {
      console.error("Copy failed:", error);
      toast({
        title: "Copy Failed",
        description: "Failed to copy to clipboard. Please try again.",
        variant: "destructive",
      });
    }
  };

  if (citations.length === 0) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant={variant} size={size} className="gap-2">
          <Download className="h-4 w-4" />
          Export ({citations.length})
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem onClick={handleCopyBibTeX}>
          {copied ? (
            <Check className="h-4 w-4 mr-2 text-green-600" />
          ) : (
            <Copy className="h-4 w-4 mr-2" />
          )}
          Copy as BibTeX
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleExport("bibtex")}>
          <Download className="h-4 w-4 mr-2" />
          Download BibTeX
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport("ris")}>
          <Download className="h-4 w-4 mr-2" />
          Download RIS
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport("csv")}>
          <Download className="h-4 w-4 mr-2" />
          Download CSV
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport("json")}>
          <Download className="h-4 w-4 mr-2" />
          Download JSON
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}


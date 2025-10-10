"use client";

import { Citation } from "@/lib/types";
import { Modal } from "@/components/ui/modal";
import { ExternalLink, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface CitationDrawerProps {
  open: boolean;
  citation: Citation | null;
  onClose: () => void;
}

export function CitationDrawer({ open, citation, onClose }: CitationDrawerProps) {
  return (
    <Modal open={open} onClose={onClose} ariaLabel="Citation details" className="max-h-[85vh] overflow-hidden">
      <div className="p-4 sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Citation</p>
            <h2 className="text-lg font-semibold leading-snug">
              {citation?.title || ""}
            </h2>
          </div>
          <button
            aria-label="Close"
            onClick={onClose}
            className="rounded-md p-2 hover:bg-muted text-muted-foreground"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {citation && (
          <div className="mt-4 space-y-4">
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              {citation.authors && citation.authors.length > 0 && (
                <span>{citation.authors.join(", ")}</span>
              )}
              {citation.journal && <span>• {citation.journal}</span>}
              {citation.publication_date && <span>• {citation.publication_date}</span>}
            </div>

            <div className="space-x-2">
              {citation.pmid && (
                <Badge variant="outline" className="text-xs">PMID: {citation.pmid}</Badge>
              )}
              {citation.nct_id && (
                <Badge variant="outline" className="text-xs">NCT: {citation.nct_id}</Badge>
              )}
              {citation.doi && (
                <Badge variant="outline" className="text-xs">DOI: {citation.doi}</Badge>
              )}
            </div>

            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {citation.snippet}
            </div>

            {citation.url && (
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
              >
                View original source
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}


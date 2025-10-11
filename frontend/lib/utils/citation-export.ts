import { Citation } from '../types/index';

/**
 * Export citations to BibTeX format
 */
export function exportToBibTeX(citations: Citation[]): string {
  return citations
    .map((c) => {
      const year = c.publication_date
        ? new Date(c.publication_date).getFullYear()
        : 'n.d.';
      const authors = c.authors?.join(' and ') || 'Unknown';
      const cleanId = c.citation_id.replace(/[^a-zA-Z0-9]/g, '_');

      return `@article{${cleanId},
  title={${c.title}},
  author={${authors}},
  journal={${c.journal || 'Unknown'}},
  year={${year}},
  doi={${c.doi || 'N/A'}},
  url={${c.url || 'N/A'}}
}`;
    })
    .join('\n\n');
}

/**
 * Export citations to RIS format (EndNote, Mendeley)
 */
export function exportToRIS(citations: Citation[]): string {
  return citations
    .map((c) => {
      const year = c.publication_date
        ? new Date(c.publication_date).getFullYear()
        : '';
      const authors = c.authors || [];

      let ris = 'TY  - JOUR\n';
      ris += `TI  - ${c.title}\n`;
      authors.forEach((author) => {
        ris += `AU  - ${author}\n`;
      });
      ris += `JO  - ${c.journal || 'Unknown'}\n`;
      if (year) ris += `PY  - ${year}\n`;
      if (c.doi) ris += `DO  - ${c.doi}\n`;
      if (c.url) ris += `UR  - ${c.url}\n`;
      ris += 'ER  - \n';

      return ris;
    })
    .join('\n');
}

/**
 * Export citations to CSV format
 */
export function exportToCSV(citations: Citation[]): string {
  const headers = [
    'ID',
    'Title',
    'Authors',
    'Source',
    'Publication Date',
    'DOI',
    'URL',
  ];

  const rows = citations.map((c) => {
    const authors = c.authors?.join('; ') || '';
    const date = c.publication_date || '';

    return [
      c.citation_id,
      `"${c.title.replace(/"/g, '""')}"`,
      `"${authors.replace(/"/g, '""')}"`,
      `"${(c.journal || 'Unknown').replace(/"/g, '""')}"`,
      date,
      c.doi || '',
      c.url || '',
    ].join(',');
  });

  return [headers.join(','), ...rows].join('\n');
}

/**
 * Export citations to JSON format
 */
export function exportToJSON(citations: Citation[]): string {
  return JSON.stringify(citations, null, 2);
}

/**
 * Download a file with the given content
 */
export function downloadFile(
  content: string,
  filename: string,
  mimeType: string = 'text/plain'
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
}

/**
 * Export citations in the specified format
 */
export function exportCitations(
  citations: Citation[],
  format: 'bibtex' | 'ris' | 'csv' | 'json'
): void {
  let content: string;
  let filename: string;
  let mimeType: string;

  switch (format) {
    case 'bibtex':
      content = exportToBibTeX(citations);
      filename = `citations_${Date.now()}.bib`;
      mimeType = 'application/x-bibtex';
      break;
    case 'ris':
      content = exportToRIS(citations);
      filename = `citations_${Date.now()}.ris`;
      mimeType = 'application/x-research-info-systems';
      break;
    case 'csv':
      content = exportToCSV(citations);
      filename = `citations_${Date.now()}.csv`;
      mimeType = 'text/csv';
      break;
    case 'json':
      content = exportToJSON(citations);
      filename = `citations_${Date.now()}.json`;
      mimeType = 'application/json';
      break;
  }

  downloadFile(content, filename, mimeType);
}


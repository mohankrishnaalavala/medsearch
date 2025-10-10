"use client";

import { useState } from "react";

export default function CitationsPage() {
  const [items] = useState([] as Array<unknown>);
  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4">Citations</h1>
      {items.length === 0 ? (
        <p className="text-muted-foreground">No citations to display yet. Run a search to populate citations.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4">{/* future: render citations */}</div>
      )}
    </main>
  );
}


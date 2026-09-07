"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import ResultsDashboard from "@/components/ResultsDashboard";
import type { AnalysisOutcome } from "@/lib/types";

export default function ResultsPage() {
  const [outcome, setOutcome] = useState<AnalysisOutcome | null | undefined>(
    undefined
  );

  useEffect(() => {
    const raw = sessionStorage.getItem("analysisOutcome");
    setOutcome(raw ? (JSON.parse(raw) as AnalysisOutcome) : null);
  }, []);

  return (
    <main>
      <Navbar />
      {outcome === undefined && (
        <p className="px-6 py-24 text-center text-navy/50">Loading…</p>
      )}
      {outcome === null && (
        <div className="px-6 py-24 text-center">
          <p className="font-display text-2xl text-navy">No analysis found</p>
          <Link
            href="/analyze"
            className="mt-6 inline-block rounded-full bg-navy px-6 py-2.5 text-sm text-white"
          >
            Analyze my business
          </Link>
        </div>
      )}
      {outcome && <ResultsDashboard outcome={outcome} />}
    </main>
  );
}

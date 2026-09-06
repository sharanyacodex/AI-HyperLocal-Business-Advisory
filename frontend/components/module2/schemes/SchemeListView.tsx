"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/module2/ui/Card";
import { Button } from "@/components/module2/ui/Button";
import { SchemeCard } from "@/components/module2/schemes/SchemeCard";
import { GovernmentScheme } from "@/types/module2/scheme";
import { MOCK_SCHEMES } from "@/lib/module2/mockSchemes";

export function SchemeListView() {
  const [status, setStatus] = useState<"loading" | "empty" | "ready" | "error">(
    "loading"
  );
  const [schemes, setSchemes] = useState<GovernmentScheme[]>([]);

  useEffect(() => {
    // Placeholder fetch — replaced by schemeService.match() (Phase 8),
    // which will call POST /schemes/match against the real backend.
    try {
      const stored = sessionStorage.getItem("module2:businessInput");
      if (!stored) {
        setStatus("empty");
        return;
      }
      setSchemes(MOCK_SCHEMES);
      setStatus(MOCK_SCHEMES.length > 0 ? "ready" : "empty");
    } catch {
      setStatus("error");
    }
  }, []);

  if (status === "loading") {
    return (
      <Card>
        <p className="text-sm text-navy/50 font-body">Matching government schemes…</p>
      </Card>
    );
  }

  if (status === "empty") {
    return (
      <Card>
        <p className="text-sm text-navy/70 font-body">
          No schemes to show yet. Complete your business details first.
        </p>
        <div className="mt-4">
          <Link href="/module2/financial">
            <Button variant="secondary">Go to business details</Button>
          </Link>
        </div>
      </Card>
    );
  }

  if (status === "error") {
    return (
      <Card>
        <p className="text-sm text-amber font-body">
          Something went wrong matching schemes. Please try again.
        </p>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <div className="flex flex-col">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.id} scheme={scheme} />
          ))}
        </div>
      </Card>

      <div>
        <Link href="/module2/recommendation">
          <Button variant="primary">Continue to final recommendation</Button>
        </Link>
      </div>
    </div>
  );
}
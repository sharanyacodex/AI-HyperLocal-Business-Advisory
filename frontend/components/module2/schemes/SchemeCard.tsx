"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/module2/ui/Card";
import { Button } from "@/components/module2/ui/Button";
import { StatusCard } from "@/components/module2/ui/StatusCard";
import { EyebrowLabel } from "@/components/module2/ui/EyebrowLabel";
import { SchemeCard } from "@/components/module2/schemes/SchemeCard";
import { BusinessInput } from "@/types/module2/financial";
import { GovernmentScheme } from "@/types/module2/scheme";
import { matchSchemes } from "@/services/module2/schemeService";

export function SchemeListView() {
  const [status, setStatus] = useState<"loading" | "empty" | "ready" | "error">(
    "loading"
  );
  const [schemes, setSchemes] = useState<GovernmentScheme[]>([]);

  useEffect(() => {
    async function load() {
      const stored = sessionStorage.getItem("module2:businessInput");
      if (!stored) {
        setStatus("empty");
        return;
      }
      try {
        const input = JSON.parse(stored) as BusinessInput;
        const matched = await matchSchemes(input);
        setSchemes(matched);
        setStatus(matched.length > 0 ? "ready" : "empty");
      } catch {
        setStatus("error");
      }
    }
    load();
  }, []);

  if (status === "loading") {
    return <StatusCard tone="loading" message="Matching government schemes…" />;
  }

  if (status === "empty") {
    return (
      <StatusCard
        tone="empty"
        message="No schemes to show yet. Complete your business details first."
        actionHref="/module2/financial"
        actionLabel="Go to business details"
      />
    );
  }

  if (status === "error") {
    return (
      <StatusCard
        tone="error"
        message="Something went wrong matching schemes. Please try again."
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <EyebrowLabel className="text-accentBlue">Local intelligence</EyebrowLabel>
        <h1 className="mt-1 mb-6 text-2xl font-semibold text-navy font-heading">
          Government schemes
        </h1>

        <div className="flex flex-col gap-3">
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
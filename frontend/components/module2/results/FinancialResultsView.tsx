"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/module2/ui/Card";
import { MetricDisplay } from "@/components/module2/ui/MetricDisplay";
import { Button } from "@/components/module2/ui/Button";
import { StatusCard } from "@/components/module2/ui/StatusCard";
import { BusinessInput, FinancialResult } from "@/types/module2/financial";
import { getFinancialFeasibility } from "@/services/module2/financialService";

function formatCurrency(value: number): string {
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export function FinancialResultsView() {
  const [status, setStatus] = useState<"loading" | "empty" | "ready" | "error">(
    "loading"
  );
  const [result, setResult] = useState<FinancialResult | null>(null);

  useEffect(() => {
    async function load() {
      const stored = sessionStorage.getItem("module2:businessInput");
      if (!stored) {
        setStatus("empty");
        return;
      }
      try {
        const input = JSON.parse(stored) as BusinessInput;
        const computed = await getFinancialFeasibility(input);
        setResult(computed);
        setStatus("ready");
      } catch {
        setStatus("error");
      }
    }
    load();
  }, []);

  if (status === "loading") {
    return <StatusCard tone="loading" message="Calculating feasibility…" />;
  }

  if (status === "empty") {
    return (
      <StatusCard
        tone="empty"
        message="We don't have your business details yet."
        actionHref="/module2/financial"
        actionLabel="Go to business details"
      />
    );
  }

  if (status === "error" || !result) {
    return (
      <StatusCard
        tone="error"
        message="Something went wrong reading your business details. Please re-enter them."
        actionHref="/module2/financial"
        actionLabel="Re-enter details"
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
          <MetricDisplay
            label="Project cost"
            value={formatCurrency(result.projectCost)}
            sublabel="Estimated 6-month working capital requirement"
          />
          <MetricDisplay
            label="Own contribution"
            value={formatCurrency(result.ownContribution)}
          />
          <MetricDisplay
            label="Loan required"
            value={formatCurrency(result.loanRequired)}
            tone="positive"
            sublabel={`${result.loanToProjectRatioPercent}% of project cost`}
          />
        </div>
      </Card>

      <Card>
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
          <MetricDisplay
            label="Monthly net surplus"
            value={formatCurrency(result.monthlyNetSurplus)}
            tone={result.monthlyNetSurplus >= 0 ? "positive" : "warning"}
            sublabel="Expected revenue minus operating costs"
          />
          <MetricDisplay
            label="Estimated break-even"
            value={
              result.breakEvenMonths !== null
                ? `${result.breakEvenMonths} months`
                : "Not achievable at current surplus"
            }
            tone={result.breakEvenMonths !== null ? "default" : "warning"}
          />
        </div>
      </Card>

      <div>
        <Link href="/module2/repayment">
          <Button variant="primary">Continue to repayment analysis</Button>
        </Link>
      </div>
    </div>
  );
}

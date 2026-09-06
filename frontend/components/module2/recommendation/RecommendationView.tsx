"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Landmark, Receipt, ShieldAlert } from "lucide-react";
import { Card } from "@/components/module2/ui/Card";
import { IconMetricCard } from "@/components/module2/ui/IconMetricCard";
import { EyebrowLabel } from "@/components/module2/ui/EyebrowLabel";
import { Button } from "@/components/module2/ui/Button";
import { StatusCard } from "@/components/module2/ui/StatusCard";
import { BusinessInput, FinancialResult } from "@/types/module2/financial";
import { RepaymentResult } from "@/types/module2/repayment";
import { FinalRecommendation } from "@/types/module2/recommendation";
import { GovernmentScheme } from "@/types/module2/scheme";
import { getFinancialFeasibility } from "@/services/module2/financialService";
import { getRepaymentRisk } from "@/services/module2/repaymentService";
import { matchSchemes } from "@/services/module2/schemeService";
import { getFinalRecommendation } from "@/services/module2/recommendationService";
import { computeRecommendationConfidence } from "@/lib/module2/mockCalculations";

function formatCurrency(value: number): string {
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export function RecommendationView() {
  const [status, setStatus] = useState<"loading" | "empty" | "ready" | "error">(
    "loading"
  );
  const [financial, setFinancial] = useState<FinancialResult | null>(null);
  const [repayment, setRepayment] = useState<RepaymentResult | null>(null);
  const [scheme, setScheme] = useState<GovernmentScheme | null>(null);
  const [recommendation, setRecommendation] = useState<FinalRecommendation | null>(null);

  useEffect(() => {
    async function load() {
      const stored = sessionStorage.getItem("module2:businessInput");
      if (!stored) {
        setStatus("empty");
        return;
      }
      try {
        const input = JSON.parse(stored) as BusinessInput;
        const financialResult = await getFinancialFeasibility(input);
        const repaymentResult = await getRepaymentRisk(input, financialResult);
        const schemes = await matchSchemes(input);
        const bestScheme =
          schemes.find((s) => s.eligibilityStatus === "eligible") ?? null;
        const finalRecommendation = await getFinalRecommendation(
          financialResult,
          repaymentResult,
          bestScheme
        );

        setFinancial(financialResult);
        setRepayment(repaymentResult);
        setScheme(bestScheme);
        setRecommendation(finalRecommendation);
        setStatus("ready");
      } catch {
        setStatus("error");
      }
    }
    load();
  }, []);

  if (status === "loading") {
    return <StatusCard tone="loading" message="Preparing your recommendation…" />;
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

  if (status === "error" || !financial || !repayment || !recommendation) {
    return (
      <StatusCard
        tone="error"
        message="Something went wrong preparing your recommendation. Please re-enter your details."
        actionHref="/module2/financial"
        actionLabel="Re-enter details"
      />
    );
  }

  const confidence = computeRecommendationConfidence(repayment.riskLevel);

  return (
    <div className="flex flex-col gap-6">
      <Card className="border-navy-deep bg-navy-deep">
        <EyebrowLabel className="text-emerald">Overall recommendation</EyebrowLabel>

        <div className="mt-3 flex flex-col gap-6 sm:flex-row sm:items-center">
          <div className="shrink-0">
            <ScoreRingDark score={confidence} label="Confidence" sublabel={recommendation.headline} />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-white font-heading">
              {recommendation.headline}
            </h1>
            <p className="mt-2 text-sm text-white/70 font-body">
              {recommendation.reasoning}
            </p>
          </div>
        </div>
      </Card>

      <div>
        <EyebrowLabel>Business signals</EyebrowLabel>
        <h3 className="mt-1 mb-4 text-lg font-semibold text-navy font-heading">
          Key figures
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <IconMetricCard
            icon={Landmark}
            value={formatCurrency(financial.loanRequired)}
            label="Loan Required"
            progressPercent={financial.loanToProjectRatioPercent}
            accent="blue"
          />
          <IconMetricCard
            icon={Receipt}
            value={formatCurrency(repayment.monthlyEmi)}
            label="Monthly EMI"
            progressPercent={repayment.monthlyEmi > 0 ? 100 : 0}
            accent="teal"
          />
          <IconMetricCard
            icon={ShieldAlert}
            value={
              repayment.riskLevel.charAt(0).toUpperCase() + repayment.riskLevel.slice(1)
            }
            label="Repayment Risk"
            progressPercent={confidence}
            accent={repayment.riskLevel === "low" ? "emerald" : "orange"}
          />
        </div>
      </div>

      <Card>
        <p className="mb-2 text-sm font-medium text-navy font-body">Matched scheme</p>
        {scheme ? (
          <div>
            <p className="text-sm text-navy font-body">{scheme.name}</p>
            <p className="mt-1 text-sm text-navy/60 font-body">{scheme.matchReason}</p>
          </div>
        ) : (
          <p className="text-sm text-navy/50 font-body">
            No eligible scheme found based on current data.
          </p>
        )}
      </Card>

      <div className="flex gap-3">
        <Link href="/module2">
          <Button variant="secondary">Back to start</Button>
        </Link>
      </div>
    </div>
  );
}

function ScoreRingDark({ score, label, sublabel }: { score: number; label: string; sublabel: string }) {
  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div className="relative flex h-32 w-32 items-center justify-center">
      <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90">
        <circle cx="64" cy="64" r={radius} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="8" />
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke="#10B981"
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute flex flex-col items-center text-center">
        <span className="font-heading text-3xl font-semibold text-white tabular-figures">
          {Math.round(clamped)}
        </span>
        <span className="text-[10px] uppercase tracking-wide text-white/50 font-body">
          {label}
        </span>
      </div>
    </div>
  );
}
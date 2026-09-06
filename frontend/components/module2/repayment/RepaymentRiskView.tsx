"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Receipt, TrendingUp, ShieldCheck } from "lucide-react";
import { Card } from "@/components/module2/ui/Card";
import { RiskMeter } from "@/components/module2/ui/RiskMeter";
import { Button } from "@/components/module2/ui/Button";
import { StatusCard } from "@/components/module2/ui/StatusCard";
import { EyebrowLabel } from "@/components/module2/ui/EyebrowLabel";
import { IconMetricCard } from "@/components/module2/ui/IconMetricCard";
import { BusinessInput } from "@/types/module2/financial";
import { RepaymentResult } from "@/types/module2/repayment";
import { getFinancialFeasibility } from "@/services/module2/financialService";
import { getRepaymentRisk } from "@/services/module2/repaymentService";

function formatCurrency(value: number): string {
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export function RepaymentRiskView() {
  const [status, setStatus] = useState<"loading" | "empty" | "ready" | "error">(
    "loading"
  );
  const [result, setResult] = useState<RepaymentResult | null>(null);

  useEffect(() => {
    async function load() {
      const stored = sessionStorage.getItem("module2:businessInput");
      if (!stored) {
        setStatus("empty");
        return;
      }
      try {
        const input = JSON.parse(stored) as BusinessInput;
        const financial = await getFinancialFeasibility(input);
        const repayment = await getRepaymentRisk(input, financial);
        setResult(repayment);
        setStatus("ready");
      } catch {
        setStatus("error");
      }
    }
    load();
  }, []);

  if (status === "loading") {
    return <StatusCard tone="loading" message="Assessing repayment risk…" />;
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
        message="Something went wrong assessing repayment risk. Please re-enter your details."
        actionHref="/module2/financial"
        actionLabel="Re-enter details"
      />
    );
  }

  const dscrProgress = result.dscr !== null ? Math.min(100, result.dscr * 40) : 100;
  const surplusProgress =
    result.operatingSurplus >= 0
      ? Math.min(100, (result.operatingSurplus / (result.monthlyEmi || 1)) * 30)
      : 0;
  const emiProgress = result.monthlyEmi > 0 ? 100 : 0;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <EyebrowLabel>Repayment intelligence</EyebrowLabel>
        <h1 className="mt-1 mb-6 text-2xl font-semibold text-navy font-heading">
          Repayment analysis
        </h1>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <IconMetricCard
            icon={Receipt}
            value={formatCurrency(result.monthlyEmi)}
            label="Monthly EMI"
            sublabel="At 11% p.a. over 36 months"
            progressPercent={emiProgress}
            accent="blue"
          />
          <IconMetricCard
            icon={TrendingUp}
            value={formatCurrency(result.operatingSurplus)}
            label="Operating Surplus"
            sublabel="Revenue minus operating costs"
            progressPercent={surplusProgress}
            accent="teal"
          />
          <IconMetricCard
            icon={ShieldCheck}
            value={result.dscr !== null ? result.dscr.toFixed(2) : "—"}
            label="DSCR"
            sublabel="Debt Service Coverage Ratio"
            progressPercent={dscrProgress}
            accent="emerald"
          />
        </div>
      </Card>

      <Card>
        <p className="mb-4 text-sm font-medium text-navy font-body">
          Repayment risk category
        </p>
        <RiskMeter level={result.riskLevel} />
        <p className="mt-4 text-sm text-navy/60 font-body">
          {result.riskExplanation}
        </p>
      </Card>

      <div>
        <Link href="/module2/schemes">
          <Button variant="primary">Continue to government schemes</Button>
        </Link>
      </div>
    </div>
  );
}
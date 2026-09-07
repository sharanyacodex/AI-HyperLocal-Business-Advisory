import type { FinancialSummary as FinancialSummaryType } from "@/lib/types";
import { formatINR, formatMonths, formatPercent } from "@/lib/format";

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="glass rounded-2xl p-6">
      <p className="font-display text-2xl text-navy">{value}</p>
      <p className="mt-1 text-sm text-navy/55">{label}</p>
    </div>
  );
}

export default function FinancialSummary({
  summary,
}: {
  summary: FinancialSummaryType | null;
}) {
  if (!summary) {
    return (
      <p className="text-navy/60">
        Financial figures aren&rsquo;t available &mdash; see the message
        above for what verified data is still needed.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <MetricCard label="Project cost" value={formatINR(summary.final_project_cost)} />
      <MetricCard label="Loan amount" value={formatINR(summary.loan_amount)} />
      <MetricCard
        label="Own contribution"
        value={formatINR(summary.beneficiary_contribution)}
      />
      <MetricCard label="Interest rate" value={formatPercent(summary.interest_rate)} />
      <MetricCard label="Tenure" value={formatMonths(summary.tenure_months)} />
      <MetricCard label="EMI" value={formatINR(summary.emi)} />
      <MetricCard label="Total interest" value={formatINR(summary.total_interest)} />
      <MetricCard
        label="Theoretical capacity"
        value={formatINR(summary.theoretical_project_capacity)}
      />
    </div>
  );
}

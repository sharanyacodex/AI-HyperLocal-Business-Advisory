import type { RepaymentSummary } from "@/lib/types";
import { formatINR, titleCase } from "@/lib/format";

const STRESS_STYLES: Record<string, string> = {
  healthy: "bg-emerald-50 text-emerald-700 border-emerald-200",
  watch: "bg-amber-50 text-amber-700 border-amber-200",
  high_stress: "bg-orange-50 text-orange-700 border-orange-200",
  very_high_stress: "bg-rose-50 text-rose-700 border-rose-200",
  not_applicable: "bg-navy/5 text-navy/60 border-navy/10",
};

export default function RepaymentRisk({
  repayment,
}: {
  repayment: RepaymentSummary;
}) {
  const badgeStyle =
    STRESS_STYLES[repayment.stress_level] ?? STRESS_STYLES.not_applicable;

  return (
    <div className="glass rounded-2xl p-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-navy/55">
            DSCR &mdash; application-level repayment stress indicator
          </p>
          <p className="font-display text-3xl text-navy">
            {repayment.dscr !== null ? repayment.dscr.toFixed(2) : "—"}
          </p>
        </div>
        <span
          className={`rounded-full border px-4 py-1.5 text-sm font-medium ${badgeStyle}`}
        >
          {titleCase(repayment.stress_level)}
        </span>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4 border-t border-navy/10 pt-6 text-sm">
        <div>
          <p className="text-navy/50">Monthly revenue</p>
          <p className="mt-1 font-medium text-navy">
            {formatINR(repayment.monthly_revenue)}
          </p>
        </div>
        <div>
          <p className="text-navy/50">Operating cost</p>
          <p className="mt-1 font-medium text-navy">
            {formatINR(repayment.monthly_operating_cost)}
          </p>
        </div>
        <div>
          <p className="text-navy/50">Operating surplus</p>
          <p className="mt-1 font-medium text-navy">
            {formatINR(repayment.operating_surplus)}
          </p>
        </div>
      </div>

      {repayment.dscr === null && (
        <p className="mt-4 text-xs text-navy/50">
          DSCR isn&rsquo;t available because the loan&rsquo;s EMI couldn&rsquo;t
          be determined from verified data.
        </p>
      )}
    </div>
  );
}

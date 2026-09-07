import type { AnalysisOutcome } from "@/lib/types";
import FinancialSummary from "./FinancialSummary";
import RepaymentRisk from "./RepaymentRisk";
import SchemeRecommendation from "./SchemeRecommendation";
import SchemeCard from "./SchemeCard";

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-12">
      <h2 className="font-display text-2xl italic text-navy">{title}</h2>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export default function ResultsDashboard({
  outcome,
}: {
  outcome: AnalysisOutcome;
}) {
  const { matches, recommendation, integration } = outcome;

  return (
    <div className="mx-auto max-w-4xl px-6 pb-24 pt-14">
      <p className="text-sm text-navy/50">Business analysis</p>
      <h1 className="mt-1 font-display text-4xl text-navy">Your results</h1>

      {integration && (
        <Section title="Financial overview">
          <FinancialSummary summary={integration.financial_summary} />
          {integration.missing_fields.length > 0 && (
            <p className="mt-4 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {integration.message}
              {" — needs: "}
              {integration.missing_fields.join(", ")}
            </p>
          )}
          {integration.used_manual_overrides.length > 0 && (
            <p className="mt-3 text-xs text-navy/50">
              Used lender-supplied values (not verified scheme data) for:{" "}
              {integration.used_manual_overrides.join(", ")}
            </p>
          )}
        </Section>
      )}

      {integration && (
        <Section title="Repayment stress">
          <RepaymentRisk repayment={integration.repayment} />
        </Section>
      )}

      <Section title="Scheme recommendation">
        <SchemeRecommendation recommendation={recommendation} />
      </Section>

      {matches.length > 0 && (
        <Section title="Matched government schemes">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            {matches.map((m) => (
              <SchemeCard
                key={String(m.scheme_code)}
                match={m}
                highlighted={m.scheme_code === recommendation.recommended_scheme_code}
              />
            ))}
          </div>
        </Section>
      )}

      <Section title="Summary">
        <div className="glass rounded-2xl p-7 text-sm leading-relaxed text-navy/70">
          {integration ? (
            <p>{integration.message}</p>
          ) : (
            <p>
              No eligible government scheme was matched for the details you
              provided. Try adjusting your business sector, location, or
              beneficiary category.
            </p>
          )}
        </div>
      </Section>
    </div>
  );
}

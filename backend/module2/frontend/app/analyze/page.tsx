"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import BusinessInputForm from "@/components/BusinessInputForm";
import AnalysisLoader from "@/components/AnalysisLoader";
import SchemeCard from "@/components/SchemeCard";
import { matchSchemes, recommendScheme, calculateIntegration } from "@/lib/api";
import type {
  BusinessInputValues,
  SchemeMatch,
  SchemeRecommendationResponse,
  AnalysisOutcome,
} from "@/lib/types";

type Stage = "form" | "loading" | "choose" | "error";

export default function AnalyzePage() {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>("form");
  const [loadingStep, setLoadingStep] = useState("Matching government schemes…");
  const [error, setError] = useState<string | null>(null);
  const [pendingMatches, setPendingMatches] = useState<SchemeMatch[]>([]);
  const [pendingRecommendation, setPendingRecommendation] =
    useState<SchemeRecommendationResponse | null>(null);
  const [pendingValues, setPendingValues] = useState<BusinessInputValues | null>(null);

  async function finalize(
    values: BusinessInputValues,
    matches: SchemeMatch[],
    recommendation: SchemeRecommendationResponse,
    schemeCode: string | null
  ) {
    let integration = null;

    if (schemeCode) {
      setLoadingStep("Calculating project cost, EMI, and repayment stress…");
      setStage("loading");
      integration = await calculateIntegration({
        requested_loan_amount: values.requested_loan_amount,
        beneficiary_category: values.beneficiary_category,
        location_type: values.location_type,
        business_sector: values.business_sector,
        tarun_plus_eligible: values.tarun_plus_eligible,
        selected_scheme_code: schemeCode,
        available_margin: values.available_margin,
        monthly_revenue: values.monthly_revenue,
        monthly_operating_cost: values.monthly_operating_cost,
      });
    }

    const outcome: AnalysisOutcome = { matches, recommendation, integration };
    sessionStorage.setItem("analysisOutcome", JSON.stringify(outcome));
    router.push("/results");
  }

  async function handleSubmit(values: BusinessInputValues) {
    setError(null);
    setStage("loading");
    setLoadingStep("Matching government schemes…");

    try {
      const matchInput = {
        requested_loan_amount: values.requested_loan_amount,
        beneficiary_category: values.beneficiary_category,
        location_type: values.location_type,
        business_sector: values.business_sector,
        tarun_plus_eligible: values.tarun_plus_eligible,
      };

      const [matchResult, recommendation] = await Promise.all([
        matchSchemes(matchInput),
        recommendScheme(matchInput),
      ]);

      const matches = matchResult.matches;

      if (matches.length === 0) {
        await finalize(values, matches, recommendation, null);
        return;
      }

      if (recommendation.recommended_scheme_code) {
        await finalize(values, matches, recommendation, recommendation.recommended_scheme_code);
        return;
      }

      // Multiple matches, backend deliberately made no automatic pick.
      setPendingMatches(matches);
      setPendingRecommendation(recommendation);
      setPendingValues(values);
      setStage("choose");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setStage("error");
    }
  }

  async function handleChoose(schemeCode: string) {
    if (!pendingValues || !pendingRecommendation) return;
    try {
      setStage("loading");
      setLoadingStep("Calculating project cost, EMI, and repayment stress…");
      await finalize(pendingValues, pendingMatches, pendingRecommendation, schemeCode);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setStage("error");
    }
  }

  return (
    <main>
      <Navbar />

      {stage === "form" && (
        <BusinessInputForm onSubmit={handleSubmit} submitting={false} />
      )}

      {stage === "loading" && <AnalysisLoader step={loadingStep} />}

      {stage === "error" && (
        <div className="mx-auto max-w-lg px-6 py-24 text-center">
          <p className="font-display text-2xl text-navy">Couldn&rsquo;t reach the server</p>
          <p className="mt-3 text-sm text-navy/60">{error}</p>
          <button
            onClick={() => setStage("form")}
            className="mt-6 rounded-full bg-navy px-6 py-2.5 text-sm text-white"
          >
            Try again
          </button>
        </div>
      )}

      {stage === "choose" && (
        <div className="mx-auto max-w-3xl px-6 py-16">
          <h1 className="font-display text-3xl text-navy">Choose a scheme to proceed</h1>
          <p className="mt-3 text-navy/60">
            {pendingRecommendation?.recommendation_reason}
          </p>
          <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2">
            {pendingMatches.map((m) => (
              <SchemeCard
                key={String(m.scheme_code)}
                match={m}
                onSelect={() => handleChoose(String(m.scheme_code))}
              />
            ))}
          </div>
        </div>
      )}
    </main>
  );
}

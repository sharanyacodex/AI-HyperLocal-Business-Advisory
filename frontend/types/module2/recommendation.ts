import { RepaymentRiskLevel, RepaymentResult } from "@/types/module2/repayment";
import { FinancialResult } from "@/types/module2/financial";
import { GovernmentScheme } from "@/types/module2/scheme";

export type RecommendationVerdict = "proceed" | "proceed_with_caution" | "not_advisable";

export interface FinalRecommendation {
  verdict: RecommendationVerdict;
  headline: string;
  reasoning: string;
}

export const VERDICT_LABELS: Record<RecommendationVerdict, string> = {
  proceed: "Proceed",
  proceed_with_caution: "Proceed with caution",
  not_advisable: "Not advisable right now",
};

export function verdictFromRisk(risk: RepaymentRiskLevel): RecommendationVerdict {
  if (risk === "low") return "proceed";
  if (risk === "moderate") return "proceed_with_caution";
  return "not_advisable";
}

export interface RecommendationRequest {
  financial: FinancialResult;
  repayment: RepaymentResult;
  matchedScheme: GovernmentScheme | null;
}
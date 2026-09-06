import { FinancialResult } from "@/types/module2/financial";
import { RepaymentResult } from "@/types/module2/repayment";
import { GovernmentScheme } from "@/types/module2/scheme";
import {
  FinalRecommendation,
  RecommendationRequest,
} from "@/types/module2/recommendation";
import { generateFinalRecommendation } from "@/lib/module2/mockCalculations";
import { apiPost, USE_MOCK_DATA } from "@/lib/api";

export async function getFinalRecommendation(
  financial: FinancialResult,
  repayment: RepaymentResult,
  matchedScheme: GovernmentScheme | null
): Promise<FinalRecommendation> {
  if (USE_MOCK_DATA) {
    return generateFinalRecommendation(repayment, matchedScheme);
  }
  return apiPost<FinalRecommendation, RecommendationRequest>(
    "/recommendation/generate",
    { financial, repayment, matchedScheme }
  );
}
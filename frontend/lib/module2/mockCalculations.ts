import { BusinessInput, FinancialResult, FinancialSignals } from "@/types/module2/financial";
import { RepaymentResult, RepaymentRiskLevel } from "@/types/module2/repayment";
import {
  FinalRecommendation,
  verdictFromRisk,
  VERDICT_LABELS,
} from "@/types/module2/recommendation";
import { GovernmentScheme } from "@/types/module2/scheme";

function clamp(value: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, value));
}

/**
 * MOCK CALCULATION — placeholder only.
 * This will be replaced by a call to POST /financial/calculate
 * against the Module 2 backend in Phase 8. Keep this function's
 * signature stable so the swap is a one-line change in the view.
 */
export function calculateFinancialFeasibility(
  input: BusinessInput
): FinancialResult {
  const workingCapitalMonths = 6;
  const projectCost = input.monthlyOperatingCosts * workingCapitalMonths;

  const ownContribution = Math.min(input.ownCapital, projectCost);
  const loanRequired = Math.max(projectCost - ownContribution, 0);

  const loanToProjectRatioPercent =
    projectCost > 0 ? Math.round((loanRequired / projectCost) * 100) : 0;

  const monthlyNetSurplus =
    input.expectedMonthlyRevenue - input.monthlyOperatingCosts;

  const breakEvenMonths =
    monthlyNetSurplus > 0 ? Math.ceil(loanRequired / monthlyNetSurplus) : null;

  return {
    projectCost,
    ownContribution,
    loanRequired,
    loanToProjectRatioPercent,
    monthlyNetSurplus,
    breakEvenMonths,
  };
}

/**
 * MOCK SIGNALS — placeholder only, for the "Business at a glance" style
 * cards. This will likely be replaced or supplemented by fields in the
 * real /financial/calculate response once the backend defines them.
 */
export function computeFinancialSignals(
  input: BusinessInput,
  financial: FinancialResult
): FinancialSignals {
  const ownContributionScore = clamp(
    financial.projectCost > 0
      ? (financial.ownContribution / financial.projectCost) * 100
      : 0
  );

  const loanCoverageScore = clamp(100 - financial.loanToProjectRatioPercent);

  const surplusScore = clamp(
    input.expectedMonthlyRevenue > 0
      ? (financial.monthlyNetSurplus / input.expectedMonthlyRevenue) * 100 + 40
      : 0
  );

  const breakEvenScore =
    financial.breakEvenMonths === null
      ? 20
      : clamp(100 - financial.breakEvenMonths * 3);

  const feasibilityScore = Math.round(
    ownContributionScore * 0.25 +
      loanCoverageScore * 0.25 +
      surplusScore * 0.3 +
      breakEvenScore * 0.2
  );

  let recommendationHeadline: string;
  let recommendationDescription: string;

  if (feasibilityScore >= 70) {
    recommendationHeadline = "Good Opportunity";
    recommendationDescription =
      "This score combines your own contribution, loan coverage, monthly surplus, and break-even speed. Your business shows strong financial feasibility.";
  } else if (feasibilityScore >= 45) {
    recommendationHeadline = "Moderate Opportunity";
    recommendationDescription =
      "This score combines your own contribution, loan coverage, monthly surplus, and break-even speed. There is a viable path, but margins are tighter than ideal.";
  } else {
    recommendationHeadline = "Needs Improvement";
    recommendationDescription =
      "This score combines your own contribution, loan coverage, monthly surplus, and break-even speed. Consider increasing own capital or reducing operating costs before proceeding.";
  }

  return {
    feasibilityScore,
    recommendationHeadline,
    recommendationDescription,
    ownContributionScore,
    loanCoverageScore,
    surplusScore,
    breakEvenScore,
  };
}

/**
 * MOCK CALCULATION — placeholder only.
 * This will be replaced by a call to POST /repayment/risk
 * against the Module 2 backend in Phase 8. Keep this function's
 * signature stable so the swap is a one-line change in the view.
 */
export function calculateRepaymentRisk(
  input: BusinessInput,
  financial: FinancialResult
): RepaymentResult {
  const annualInterestRate = 0.11;
  const tenureMonths = 36;
  const monthlyRate = annualInterestRate / 12;

  const monthlyEmi =
    financial.loanRequired > 0
      ? (financial.loanRequired *
          monthlyRate *
          Math.pow(1 + monthlyRate, tenureMonths)) /
        (Math.pow(1 + monthlyRate, tenureMonths) - 1)
      : 0;

  const operatingSurplus =
    input.expectedMonthlyRevenue - input.monthlyOperatingCosts;

  const dscr = monthlyEmi > 0 ? operatingSurplus / monthlyEmi : null;

  let riskLevel: RepaymentRiskLevel;
  let riskExplanation: string;

  if (dscr === null) {
    riskLevel = "low";
    riskExplanation =
      "No loan repayment is required based on the current inputs.";
  } else if (dscr >= 1.5) {
    riskLevel = "low";
    riskExplanation =
      "Your operating surplus comfortably covers the EMI, with a healthy buffer.";
  } else if (dscr >= 1.1) {
    riskLevel = "moderate";
    riskExplanation =
      "Your operating surplus covers the EMI, but the buffer is limited.";
  } else {
    riskLevel = "high";
    riskExplanation =
      "Your operating surplus may not reliably cover the EMI. Consider reducing the loan amount or increasing own contribution.";
  }

  return {
    monthlyEmi,
    operatingSurplus,
    dscr,
    riskLevel,
    riskExplanation,
  };
}

/**
 * MOCK LOGIC — placeholder only.
 * This will be replaced by a call to POST /recommendation/generate
 * against the Module 2 backend in Phase 8. Keep this function's
 * signature stable so the swap is a one-line change in the view.
 */
export function generateFinalRecommendation(
  repayment: RepaymentResult,
  bestScheme: GovernmentScheme | null
): FinalRecommendation {
  const verdict = verdictFromRisk(repayment.riskLevel);

  let reasoning = repayment.riskExplanation;
  if (bestScheme && bestScheme.eligibilityStatus === "eligible") {
    reasoning += ` You may also qualify for ${bestScheme.name}, which can improve your funding position.`;
  }

  return {
    verdict,
    headline: VERDICT_LABELS[verdict],
    reasoning,
  };
}

/**
 * MOCK SIGNAL — placeholder only. Maps repayment risk to a 0-100
 * confidence figure for the recommendation score ring. Will likely
 * be replaced by a field in the real /recommendation/generate
 * response in Phase 8.
 */
export function computeRecommendationConfidence(
  riskLevel: RepaymentRiskLevel
): number {
  if (riskLevel === "low") return 85;
  if (riskLevel === "moderate") return 55;
  return 25;
}
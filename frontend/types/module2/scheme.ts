export type SchemeEligibilityStatus = "eligible" | "not_eligible" | "review_needed";

export interface GovernmentScheme {
  id: string;
  name: string;
  eligibilityStatus: SchemeEligibilityStatus;
  matchReason: string;
  loanOrSubsidyInfo?: string;
  detailsUrl?: string;
}

export const ELIGIBILITY_LABELS: Record<SchemeEligibilityStatus, string> = {
  eligible: "Eligible",
  not_eligible: "Not eligible",
  review_needed: "Needs review",
};
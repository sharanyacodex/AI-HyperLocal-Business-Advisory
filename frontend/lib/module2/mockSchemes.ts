import { GovernmentScheme } from "@/types/module2/scheme";

/**
 * MOCK DATA — placeholder only, for frontend development.
 *
 * This is NOT the final scheme dataset. The Module 2 backend
 * developer is still adding two more government-scheme data
 * files, and the real list will come from:
 *   GET /schemes
 *   POST /schemes/match
 *
 * Do not extend this list to "complete" it — replace this whole
 * file's usage with the real service call in Phase 8 instead.
 */
export const MOCK_SCHEMES: GovernmentScheme[] = [
  {
    id: "mock-pmegp",
    name: "PMEGP (sample)",
    eligibilityStatus: "eligible",
    matchReason:
      "Sample match based on business category and requested loan amount.",
    loanOrSubsidyInfo: "Sample subsidy: up to 25% of project cost.",
  },
  {
    id: "mock-mudra",
    name: "MUDRA Loan (sample)",
    eligibilityStatus: "review_needed",
    matchReason:
      "Sample: loan amount is close to the category threshold and needs backend confirmation.",
  },
  {
    id: "mock-standup-india",
    name: "Stand-Up India (sample)",
    eligibilityStatus: "not_eligible",
    matchReason: "Sample: category criteria not met in this placeholder data.",
  },
];
// Mirrors backend Pydantic models exactly. Do not add fields the
// backend does not return; do not invent fields it does not accept.

export interface SchemeMatchingInput {
  requested_loan_amount: number;
  beneficiary_category: string;
  location_type: string;
  business_sector: string;
  tarun_plus_eligible?: boolean;
}

// Match dict shape varies by scheme (PMMY vs PMEGP return different
// keys) -- backend returns list[dict], so this stays loosely typed.
export type SchemeMatch = Record<string, string | number | boolean | null>;

export interface SchemeMatchResponse {
  success: boolean;
  requested_loan_amount: number;
  total_matches: number;
  matches: SchemeMatch[];
}

export interface SchemeRecommendationResponse {
  success: boolean;
  total_matches: number;
  recommended_scheme_code: string | null;
  recommended_scheme_name: string | null;
  recommendation_reason: string;
}

export interface ManualOverrides {
  contribution_rate?: number;
  project_cost_limit?: number;
  loan_limit?: number;
  interest_rate?: number;
  tenure_months?: number;
}

export interface IntegrationInput extends SchemeMatchingInput {
  selected_scheme_code: string;
  available_margin: number;
  monthly_revenue: number;
  monthly_operating_cost: number;
  manual_overrides?: ManualOverrides;
}

export interface FinancialSummary {
  theoretical_project_capacity: number;
  final_project_cost: number;
  beneficiary_contribution: number;
  loan_amount: number;
  interest_rate: number | null;
  tenure_months: number | null;
  emi: number | null;
  total_interest: number | null;
}

export interface RepaymentSummary {
  monthly_revenue: number;
  monthly_operating_cost: number;
  operating_surplus: number;
  dscr: number | null;
  stress_level: string;
}

export interface IntegrationResponse {
  success: boolean;
  selected_scheme_code: string;
  scheme_match: SchemeMatch;
  financial_summary: FinancialSummary | null;
  repayment: RepaymentSummary;
  missing_fields: string[];
  used_manual_overrides: string[];
  subsidy_rate: number | null;
  message: string;
}

// Business input form values (superset used to build the API calls).
export interface BusinessInputValues {
  requested_loan_amount: number;
  beneficiary_category: string;
  location_type: string;
  business_sector: string;
  tarun_plus_eligible: boolean;
  available_margin: number;
  monthly_revenue: number;
  monthly_operating_cost: number;
}

// What gets stored between the analyze step and the results page.
export interface AnalysisOutcome {
  matches: SchemeMatch[];
  recommendation: SchemeRecommendationResponse;
  integration: IntegrationResponse | null;
}

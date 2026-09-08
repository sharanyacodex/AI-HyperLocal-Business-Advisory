/**
 * VyaparDisha - Module 2: Financial and Scheme Planning
 * Type definitions matching the EXISTING FastAPI / Pydantic backend.
 *
 * IMPORTANT: These field names are taken verbatim from a confirmed working
 * request payload provided by the backend owner. Do not rename these fields
 * to "friendlier" names — the backend is the source of truth.
 */

export interface ManualOverrides {
  contribution_rate: number;
  project_cost_limit: number;
  loan_limit: number;
  interest_rate: number;
  tenure_months: number;
}

export interface FinancialPlanRequest {
  requested_loan_amount: number;
  beneficiary_category: string; // e.g. "general"
  location_type: string; // e.g. "rural" | "urban"
  business_sector: string; // e.g. "manufacturing"
  tarun_plus_eligible: boolean;
  selected_scheme_code: string; // e.g. "PMEGP"
  available_margin: number;
  monthly_revenue: number;
  monthly_operating_cost: number;
  manual_overrides?: ManualOverrides;
}

/**
 * The response shape is intentionally NOT hard-typed field-by-field.
 * We only know the backend's confirmed top-level sections from the product
 * spec (financial_summary, repayment, scheme_match, subsidy_information,
 * recommendation). We do not know every nested field name yet, so each
 * section is typed as a generic record and rendered dynamically in the UI
 * rather than guessed at. Once you share a real sample response, this can
 * be tightened to exact fields.
 */
export type ResponseSection = Record<string, unknown> | null | undefined;

export interface Module2CalculateResponse {
  financial_summary?: ResponseSection;
  repayment?: ResponseSection;
  scheme_match?: ResponseSection;
  subsidy_information?: ResponseSection;
  recommendation?: ResponseSection | string;

  // Allow any other top-level keys the backend sends without breaking types
  [key: string]: unknown;
}

export interface ApiErrorResponse {
  detail?: string | Array<{ loc: string[]; msg: string; type: string }>;
  message?: string;
  error?: string;
}

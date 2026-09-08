/**
 * VyaparDisha - Module 2 API Client
 * Primary Endpoint: POST /api/module2/integration/calculate
 *
 * This client does NOT calculate, normalize, guess, or reshape any
 * financial figures. The FastAPI backend is the sole source of truth for
 * EMI, DSCR, subsidy, and scheme-matching logic. The frontend only sends
 * the confirmed request payload and renders whatever the backend returns.
 */

import { FinancialPlanRequest, Module2CalculateResponse } from '../types/module2';

const STORAGE_KEY_API_BASE = 'vyapardisha_api_base_url';

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(STORAGE_KEY_API_BASE);
    if (saved) return saved.replace(/\/$/, '');
  }

  const metaEnv = (import.meta as any)?.env;
  const viteUrl = metaEnv?.VITE_API_BASE_URL || metaEnv?.NEXT_PUBLIC_API_BASE_URL;
  if (viteUrl) return viteUrl.replace(/\/$/, '');

  const nextUrl = typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_BASE_URL;
  if (nextUrl) return nextUrl.replace(/\/$/, '');

  return 'http://127.0.0.1:8000';
}

export function setApiBaseUrl(url: string): void {
  if (typeof window !== 'undefined') {
    const sanitized = url.trim().replace(/\/$/, '');
    localStorage.setItem(STORAGE_KEY_API_BASE, sanitized);
  }
}

export function resetApiBaseUrl(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(STORAGE_KEY_API_BASE);
  }
}

/**
 * Main API call: POST /api/module2/integration/calculate
 * Sends the exact request payload and returns the backend's JSON response
 * untouched (aside from basic error-shape handling for network/HTTP errors).
 */
export async function calculateFinancialPlan(
  payload: FinancialPlanRequest
): Promise<Module2CalculateResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/module2/integration/calculate`;

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch (err: any) {
    throw new Error(
      `Unable to reach FastAPI backend at ${baseUrl}. Confirm the server is running (uvicorn main:app --reload --port 8000) and that CORS allows this origin.`
    );
  }

  if (!response.ok) {
    let errorMessage = `Backend returned status ${response.status}`;
    try {
      const errorJson = await response.json();
      if (typeof errorJson.detail === 'string') {
        errorMessage = errorJson.detail;
      } else if (Array.isArray(errorJson.detail)) {
        // FastAPI / Pydantic validation error format
        errorMessage = errorJson.detail
          .map((err: any) => `${err.loc?.slice(-1)[0] || 'field'}: ${err.msg}`)
          .join('; ');
      } else if (errorJson.message) {
        errorMessage = errorJson.message;
      }
    } catch {
      // use fallback status message
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return data as Module2CalculateResponse;
}

/**
 * The one confirmed-working sample payload, for prefilling the form or
 * for a quick "load known-good example" action. This does NOT simulate a
 * backend response — it only fills the request form.
 */
export const KNOWN_GOOD_SAMPLE_REQUEST: FinancialPlanRequest = {
  requested_loan_amount: 500000,
  beneficiary_category: 'general',
  location_type: 'rural',
  business_sector: 'manufacturing',
  tarun_plus_eligible: false,
  selected_scheme_code: 'PMEGP',
  available_margin: 100000,
  monthly_revenue: 150000,
  monthly_operating_cost: 90000,
  manual_overrides: {
    contribution_rate: 0.1,
    project_cost_limit: 5000000,
    loan_limit: 4500000,
    interest_rate: 8,
    tenure_months: 84,
  },
};

import type {
  SchemeMatchingInput,
  SchemeMatchResponse,
  SchemeRecommendationResponse,
  IntegrationInput,
  IntegrationResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function post<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = `Request to ${path} failed (${res.status}).`;
    try {
      const errBody = await res.json();
      if (errBody?.detail) detail = String(errBody.detail);
    } catch {
      // response wasn't JSON; keep default message
    }
    throw new Error(detail);
  }

  return res.json() as Promise<TResponse>;
}

export function matchSchemes(input: SchemeMatchingInput) {
  return post<SchemeMatchResponse>("/api/v1/schemes/match", input);
}

export function recommendScheme(input: SchemeMatchingInput) {
  return post<SchemeRecommendationResponse>(
    "/api/module2/recommendation/recommend",
    input
  );
}

export function calculateIntegration(input: IntegrationInput) {
  return post<IntegrationResponse>("/api/module2/integration/calculate", input);
}

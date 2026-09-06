import { BusinessInput } from "@/types/module2/financial";
import { GovernmentScheme, SchemeMatchRequest } from "@/types/module2/scheme";
import { MOCK_SCHEMES } from "@/lib/module2/mockSchemes";
import { apiGet, apiPost, USE_MOCK_DATA } from "@/lib/api";

export async function matchSchemes(
  input: BusinessInput
): Promise<GovernmentScheme[]> {
  if (USE_MOCK_DATA) {
    return MOCK_SCHEMES;
  }
  return apiPost<GovernmentScheme[], SchemeMatchRequest>("/schemes/match", {
    input,
  });
}

export async function getAllSchemes(): Promise<GovernmentScheme[]> {
  if (USE_MOCK_DATA) {
    return MOCK_SCHEMES;
  }
  return apiGet<GovernmentScheme[]>("/schemes");
}

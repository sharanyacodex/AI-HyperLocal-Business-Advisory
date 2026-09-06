import { BusinessInput, FinancialResult } from "@/types/module2/financial";
import { calculateFinancialFeasibility } from "@/lib/module2/mockCalculations";
import { apiPost, USE_MOCK_DATA } from "@/lib/api";

export async function getFinancialFeasibility(
  input: BusinessInput
): Promise<FinancialResult> {
  if (USE_MOCK_DATA) {
    return calculateFinancialFeasibility(input);
  }
  return apiPost<FinancialResult, BusinessInput>("/financial/calculate", input);
}

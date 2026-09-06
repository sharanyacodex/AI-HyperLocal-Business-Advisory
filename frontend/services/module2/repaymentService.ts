import { BusinessInput, FinancialResult } from "@/types/module2/financial";
import { RepaymentResult, RepaymentRiskRequest } from "@/types/module2/repayment";
import { calculateRepaymentRisk } from "@/lib/module2/mockCalculations";
import { apiPost, USE_MOCK_DATA } from "@/lib/api";

export async function getRepaymentRisk(
  input: BusinessInput,
  financial: FinancialResult
): Promise<RepaymentResult> {
  if (USE_MOCK_DATA) {
    return calculateRepaymentRisk(input, financial);
  }
  return apiPost<RepaymentResult, RepaymentRiskRequest>("/repayment/risk", {
    input,
    financial,
  });
}
export type BusinessCategory =
  | "retail"
  | "food_and_beverage"
  | "manufacturing"
  | "services"
  | "agriculture"
  | "other";

export interface BusinessInput {
  location: string;
  businessCategory: BusinessCategory;
  ownCapital: number;
  expectedMonthlyRevenue: number;
  monthlyOperatingCosts: number;
  existingDebt: number;
  existingAssetsValue: number;
  experienceYears: number;
  numberOfWorkers: number;
}

export const BUSINESS_CATEGORY_OPTIONS: { value: BusinessCategory; label: string }[] = [
  { value: "retail", label: "Retail / Trading" },
  { value: "food_and_beverage", label: "Food & Beverage" },
  { value: "manufacturing", label: "Manufacturing" },
  { value: "services", label: "Services" },
  { value: "agriculture", label: "Agriculture" },
  { value: "other", label: "Other" },
];

export interface FinancialResult {
  projectCost: number;
  ownContribution: number;
  loanRequired: number;
  loanToProjectRatioPercent: number;
  monthlyNetSurplus: number;
  breakEvenMonths: number | null;
}
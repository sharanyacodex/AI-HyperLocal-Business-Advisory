export interface FlowStep {
  id: string;
  label: string;
  href: string;
}

export const MODULE2_FLOW_STEPS: FlowStep[] = [
  { id: "business", label: "Business Details", href: "/module2/financial" },
  { id: "financial", label: "Financial Analysis", href: "/module2/results" },
  { id: "repayment", label: "Repayment Risk", href: "/module2/repayment" },
  { id: "schemes", label: "Government Schemes", href: "/module2/schemes" },
  { id: "recommendation", label: "Recommendation", href: "/module2/recommendation" },
];

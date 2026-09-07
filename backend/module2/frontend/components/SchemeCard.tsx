import type { SchemeMatch } from "@/lib/types";
import { formatINR, formatPercent, formatMonths, titleCase } from "@/lib/format";

const FIELD_LABELS: Record<string, (v: any) => string> = {
  category: (v) => titleCase(String(v)),
  maximum_loan_amount: (v) => formatINR(Number(v)),
  maximum_project_cost: (v) => formatINR(Number(v)),
  contribution_rate: (v) => formatPercent(Number(v) * 100),
  bank_financing_rate: (v) => formatPercent(Number(v) * 100),
  subsidy_rate: (v) => formatPercent(Number(v) * 100),
  interest_rate: (v) => formatPercent(Number(v)),
  tenure_months: (v) => formatMonths(Number(v)),
  beneficiary_category: (v) => titleCase(String(v)),
  location_type: (v) => titleCase(String(v)),
  business_sector: (v) => titleCase(String(v)),
};

const FIELD_ORDER = [
  "category",
  "maximum_loan_amount",
  "maximum_project_cost",
  "contribution_rate",
  "bank_financing_rate",
  "subsidy_rate",
  "interest_rate",
  "tenure_months",
];

export default function SchemeCard({
  match,
  highlighted,
  onSelect,
}: {
  match: SchemeMatch;
  highlighted?: boolean;
  onSelect?: () => void;
}) {
  const rows = FIELD_ORDER.filter(
    (key) => match[key] !== null && match[key] !== undefined
  );

  return (
    <div
      className={`glass rounded-2xl p-6 ${
        highlighted ? "ring-2 ring-skyaccent" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-navy/40">
            {String(match.scheme_code ?? "")}
          </p>
          <h3 className="font-display text-xl text-navy">
            {String(match.scheme_name ?? match.scheme_code ?? "Scheme")}
          </h3>
        </div>
        {highlighted && (
          <span className="rounded-full bg-skyaccent/10 px-3 py-1 text-xs font-medium text-skyaccent">
            Recommended
          </span>
        )}
      </div>

      {rows.length > 0 && (
        <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
          {rows.map((key) => (
            <div key={key}>
              <dt className="text-navy/45">{titleCase(key)}</dt>
              <dd className="mt-0.5 font-medium text-navy">
                {FIELD_LABELS[key](match[key])}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {match.message && (
        <p className="mt-4 text-xs text-navy/55">{String(match.message)}</p>
      )}

      {onSelect && (
        <button
          onClick={onSelect}
          className="mt-5 w-full rounded-full border border-navy/20 py-2 text-sm font-medium text-navy transition hover:border-navy hover:bg-navy hover:text-white"
        >
          Use this scheme
        </button>
      )}
    </div>
  );
}

import React from 'react';

/**
 * Renders whatever key/value pairs the backend actually returns for a
 * response section, without assuming specific field names. This exists
 * because we do not yet have a confirmed sample response payload — once
 * you share one, these can be swapped for hard-typed, precisely labeled
 * fields if you'd prefer that over the generic grid.
 */

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function looksLikeCurrency(key: string): boolean {
  return /amount|cost|capital|revenue|margin|loan|emi|price|value|contribution|limit/i.test(key);
}

function looksLikePercent(key: string): boolean {
  return /rate|percent|pct|dscr|score/i.test(key);
}

function formatValue(key: string, value: unknown): React.ReactNode {
  if (value === null || value === undefined || value === '') {
    return <span className="text-slate-300">—</span>;
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (typeof value === 'number') {
    if (looksLikeCurrency(key)) {
      return '₹' + Math.round(value).toLocaleString('en-IN');
    }
    if (looksLikePercent(key)) {
      return value.toLocaleString('en-IN', { maximumFractionDigits: 2 });
    }
    return value.toLocaleString('en-IN');
  }
  if (Array.isArray(value)) {
    return (
      <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
        {value.map((item, i) => (
          <li key={i}>{typeof item === 'object' ? JSON.stringify(item) : String(item)}</li>
        ))}
      </ul>
    );
  }
  if (typeof value === 'object') {
    return <DynamicFieldGrid data={value as Record<string, unknown>} nested />;
  }
  return String(value);
}

interface DynamicFieldGridProps {
  data: Record<string, unknown> | null | undefined;
  nested?: boolean;
}

export const DynamicFieldGrid: React.FC<DynamicFieldGridProps> = ({ data, nested }) => {
  if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
    return <p className="text-sm text-slate-400 italic">No data returned for this section.</p>;
  }

  const entries = Object.entries(data);

  return (
    <div className={nested ? 'mt-2 pl-3 border-l-2 border-slate-100 space-y-2' : 'grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4'}>
      {entries.map(([key, value]) => (
        <div key={key}>
          <p className="text-[10px] text-slate-400 uppercase font-bold mb-0.5">{humanizeKey(key)}</p>
          <div className="text-sm font-semibold text-slate-800 font-mono break-words">
            {formatValue(key, value)}
          </div>
        </div>
      ))}
    </div>
  );
};

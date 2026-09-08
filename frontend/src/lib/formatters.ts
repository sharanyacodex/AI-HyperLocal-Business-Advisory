/**
 * Formatting utilities for Indian Rupee currency and percentages
 */

export function formatINR(val: number | string | null | undefined): string {
  if (val === null || val === undefined || isNaN(Number(val))) return '₹0';
  const num = Math.round(Number(val));
  return '₹' + num.toLocaleString('en-IN');
}

export function formatPercent(val: number | string | null | undefined): string {
  if (val === null || val === undefined || isNaN(Number(val))) return '—';
  return `${Number(val).toFixed(Number(val) % 1 === 0 ? 0 : 2)}%`;
}

export function formatMonths(months: number | null | undefined): string {
  if (!months || isNaN(months)) return '—';
  const years = Math.floor(months / 12);
  const rem = months % 12;
  if (years > 0 && rem === 0) {
    return `${months} months (${years} yr${years > 1 ? 's' : ''})`;
  } else if (years > 0) {
    return `${months} months (${years}y ${rem}m)`;
  }
  return `${months} months`;
}

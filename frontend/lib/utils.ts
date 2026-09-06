/**
 * Minimal class name combiner.
 * Joins truthy class values without pulling in an extra dependency.
 */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
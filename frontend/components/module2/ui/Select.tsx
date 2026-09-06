import { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: SelectOption[];
  error?: string;
}

export function Select({
  label,
  options,
  error,
  className,
  id,
  ...props
}: SelectProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-navy font-body">
        {label}
      </label>
      <select
        id={id}
        className={cn(
          "rounded border bg-surface px-3 py-2.5 text-sm text-navy font-body",
          "focus:border-emerald focus:outline-none",
          error ? "border-amber" : "border-border",
          className
        )}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className="text-xs text-amber font-body">{error}</p>}
    </div>
  );
}
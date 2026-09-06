import { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string;
}

export function FormField({
  label,
  hint,
  error,
  className,
  id,
  ...props
}: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-navy font-body">
        {label}
      </label>
      <input
        id={id}
        className={cn(
          "rounded border bg-surface px-3 py-2.5 text-sm text-navy font-body tabular-figures placeholder:text-navy/30",
          "focus:border-emerald focus:outline-none",
          error ? "border-amber" : "border-border",
          className
        )}
        {...props}
      />
      {error ? (
        <p className="text-xs text-amber font-body">{error}</p>
      ) : hint ? (
        <p className="text-xs text-navy/50 font-body">{hint}</p>
      ) : null}
    </div>
  );
}
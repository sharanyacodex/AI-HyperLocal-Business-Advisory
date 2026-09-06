import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "highlight" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-emerald text-white hover:bg-emerald-hover disabled:opacity-50",
  secondary:
    "bg-transparent text-navy border border-border hover:bg-navy/5 disabled:opacity-50",
  highlight:
    "bg-amber text-white hover:bg-amber-hover disabled:opacity-50",
  ghost:
    "bg-transparent text-navy hover:bg-navy/5 disabled:opacity-50",
};

export function Button({
  variant = "primary",
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded px-4 py-2.5 text-sm font-medium font-body transition-colors disabled:cursor-not-allowed",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

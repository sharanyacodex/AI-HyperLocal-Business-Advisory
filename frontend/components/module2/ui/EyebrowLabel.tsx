interface EyebrowLabelProps {
  children: React.ReactNode;
  className?: string;
}

export function EyebrowLabel({ children, className = "text-emerald" }: EyebrowLabelProps) {
  return (
    <p className={`text-xs font-semibold uppercase tracking-wide font-body ${className}`}>
      {children}
    </p>
  );
}
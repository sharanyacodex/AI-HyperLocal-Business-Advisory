import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

interface PageContainerProps extends HTMLAttributes<HTMLDivElement> {}

export function PageContainer({
  className,
  children,
  ...props
}: PageContainerProps) {
  return (
    <div
      className={cn("mx-auto w-full max-w-content px-6 py-10", className)}
      {...props}
    >
      {children}
    </div>
  );
}

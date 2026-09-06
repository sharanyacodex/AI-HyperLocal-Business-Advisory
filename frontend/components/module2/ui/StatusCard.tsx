import Link from "next/link";
import { Card } from "@/components/module2/ui/Card";
import { Button } from "@/components/module2/ui/Button";

type StatusTone = "loading" | "empty" | "error";

interface StatusCardProps {
  tone: StatusTone;
  message: string;
  actionHref?: string;
  actionLabel?: string;
}

const toneTextStyles: Record<StatusTone, string> = {
  loading: "text-navy/50",
  empty: "text-navy/70",
  error: "text-amber",
};

export function StatusCard({ tone, message, actionHref, actionLabel }: StatusCardProps) {
  return (
    <Card>
      <p className={`text-sm font-body ${toneTextStyles[tone]}`}>{message}</p>
      {actionHref && actionLabel && (
        <div className="mt-4">
          <Link href={actionHref}>
            <Button variant="secondary">{actionLabel}</Button>
          </Link>
        </div>
      )}
    </Card>
  );
}
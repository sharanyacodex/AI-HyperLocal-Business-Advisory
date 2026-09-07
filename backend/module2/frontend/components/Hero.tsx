import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-20 pt-16 md:pt-24">
      <div className="max-w-2xl">
        <h1 className="font-display text-4xl leading-[1.15] text-navy md:text-6xl">
          Financial clarity for the{" "}
          <span className="italic">next enterprise</span> in your village.
        </h1>
        <p className="mt-6 max-w-lg text-lg text-navy/70">
          Enter your business numbers once. Get a project cost, loan
          structure, repayment outlook, and the government schemes you
          actually qualify for &mdash; calculated deterministically, not
          guessed.
        </p>
        <div className="mt-9 flex items-center gap-5">
          <Link
            href="/analyze"
            className="group flex items-center gap-2 rounded-full bg-navy px-7 py-3.5 text-white transition hover:bg-navy-600"
          >
            Analyze my business
            <ArrowRight
              size={18}
              className="transition group-hover:translate-x-0.5"
            />
          </Link>
        </div>
      </div>

      <dl className="mt-20 grid grid-cols-1 gap-8 border-t border-navy/10 pt-10 sm:grid-cols-3">
        <div>
          <dt className="font-display text-3xl text-navy">PMMY + PMEGP</dt>
          <dd className="mt-1 text-sm text-navy/60">
            Matched against actual scheme rules, not assumptions
          </dd>
        </div>
        <div>
          <dt className="font-display text-3xl text-navy">Deterministic</dt>
          <dd className="mt-1 text-sm text-navy/60">
            Every figure traces back to a fixed, auditable formula
          </dd>
        </div>
        <div>
          <dt className="font-display text-3xl text-navy">No ML guesswork</dt>
          <dd className="mt-1 text-sm text-navy/60">
            No forecasting, no black box &mdash; just your numbers
          </dd>
        </div>
      </dl>
    </section>
  );
}

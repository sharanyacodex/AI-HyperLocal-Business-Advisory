import Link from "next/link";
import { Landmark } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-navy/5 bg-paper/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-navy">
          <Landmark size={22} strokeWidth={1.75} />
          <span className="font-display text-lg italic">Sahayak</span>
        </Link>
        <Link
          href="/analyze"
          className="rounded-full bg-navy px-5 py-2 text-sm font-medium text-white transition hover:bg-navy-600"
        >
          Analyze my business
        </Link>
      </div>
    </header>
  );
}

import Link from "next/link";

export default function CookiePolicyPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-10 md:px-6">
      <section className="page-surface px-6 py-8 md:px-10">
        <span className="section-label">Legal</span>
        <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-950">
          Cookie Policy
        </h1>
        <p className="mt-4 text-base leading-8 text-slate-600">
          Underlytics uses essential session and product-behavior cookies to support
          authentication, secure navigation, and application workflow continuity.
          Additional analytics or marketing disclosures can be added here when they are
          introduced.
        </p>
        <p className="mt-4 text-base leading-8 text-slate-600">
          This is a temporary policy placeholder that keeps the public legal links
          functional while formal policy text is prepared.
        </p>
        <Link href="/" className="mt-8 inline-flex text-sm font-medium text-indigo-700">
          Return to Underlytics
        </Link>
      </section>
    </main>
  );
}

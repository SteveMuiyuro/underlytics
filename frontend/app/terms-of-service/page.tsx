import Link from "next/link";

export default function TermsOfServicePage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-10 md:px-6">
      <section className="page-surface px-6 py-8 md:px-10">
        <span className="section-label">Legal</span>
        <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-950">
          Terms of Service
        </h1>
        <p className="mt-4 text-base leading-8 text-slate-600">
          Underlytics provides application intake, underwriting workflow orchestration,
          document handling, and reviewer collaboration features for lending operations.
          Platform use is subject to authorized access, acceptable use constraints, and
          institution-specific underwriting policies.
        </p>
        <p className="mt-4 text-base leading-8 text-slate-600">
          This route is a placeholder so the redesigned public footer points to a valid
          legal destination until the final terms are supplied.
        </p>
        <Link href="/" className="mt-8 inline-flex text-sm font-medium text-indigo-700">
          Return to Underlytics
        </Link>
      </section>
    </main>
  );
}

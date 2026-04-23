import Link from "next/link";

export default function PrivacyPolicyPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-10 md:px-6">
      <section className="page-surface px-6 py-8 md:px-10">
        <span className="section-label">Legal</span>
        <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-950">
          Privacy Policy
        </h1>
        <p className="mt-4 text-base leading-8 text-slate-600">
          Underlytics processes applicant identity, financial, and document data for
          underwriting, fraud checks, and audit-ready workflow history. Access is
          role-scoped, activity is recorded, and sensitive review actions stay within
          authenticated product workflows.
        </p>
        <p className="mt-4 text-base leading-8 text-slate-600">
          This page is currently a product placeholder for legal review. It exists so
          the public experience has a valid destination for privacy disclosures while
          the full policy is being finalized.
        </p>
        <Link href="/" className="mt-8 inline-flex text-sm font-medium text-indigo-700">
          Return to Underlytics
        </Link>
      </section>
    </main>
  );
}

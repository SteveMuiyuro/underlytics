import Link from "next/link";
import { auth } from "@clerk/nextjs/server";
import {
  ArrowRight,
  BadgeCheck,
  ChartColumnIncreasing,
  FileCheck2,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";

import AdminBootstrapPanel from "@/components/admin/admin-bootstrap-panel";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { getBackendActor } from "@/lib/api/server-actor";

const features = [
  {
    title: "Planner + worker orchestration",
    description:
      "Structured underwriting workflows route applications through specialized evaluators with deterministic coordination.",
    icon: Workflow,
  },
  {
    title: "Explainable decisions",
    description:
      "Scores, confidence, reasoning, and flags stay visible so teams understand how each decision was formed.",
    icon: Sparkles,
  },
  {
    title: "Document-first application flow",
    description:
      "Applicants submit evidence in one guided workspace while reviewers monitor completeness and quality in real time.",
    icon: FileCheck2,
  },
  {
    title: "Enterprise-ready controls",
    description:
      "Role-aware access, audit-friendly workflows, and clean handoffs between automation and manual review.",
    icon: ShieldCheck,
  },
];

const metrics = [
  { value: "5", label: "specialized workers orchestrated per case" },
  { value: "100%", label: "structured JSON outputs across agents" },
  { value: "1", label: "shared workspace for applicants and reviewers" },
];

const steps = [
  "Applicant submits a structured application and uploads core documents.",
  "The planner coordinates document, policy, risk, and fraud workers in sequence.",
  "Underlytics returns an explainable approval, rejection, or manual review path.",
];

function ActionButtons({ userId }: { userId: string | null }) {
  if (userId) {
    return (
      <Link href="/dashboard">
        <Button className="h-11 rounded-2xl px-5">
          Go to Dashboard
          <ArrowRight className="size-4" />
        </Button>
      </Link>
    );
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <Link href="/sign-up">
        <Button className="h-11 rounded-2xl px-5">
          Register
          <ArrowRight className="size-4" />
        </Button>
      </Link>

      <Link href="/sign-in">
        <Button variant="outline" className="h-11 rounded-2xl px-5">
          Sign In
        </Button>
      </Link>
    </div>
  );
}

export default async function Home() {
  const { userId } = await auth();
  let actorRole: string | null = null;

  try {
    const actor = await getBackendActor();
    actorRole = actor.role;
  } catch {
    actorRole = null;
  }

  return (
    <main className="min-h-screen">
      <section className="mx-auto flex min-h-screen max-w-[1440px] flex-col px-4 py-4 md:px-6 xl:px-8">
        <div className="page-surface flex min-h-[calc(100vh-2rem)] flex-col overflow-hidden">
          <header className="border-b border-slate-200/70 px-6 py-5 md:px-10">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <Link href="/" className="flex items-center gap-3">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-slate-950 text-white">
                  <Sparkles className="size-5" />
                </div>
                <div>
                  <p className="font-heading text-lg font-semibold text-slate-950">
                    Underlytics
                  </p>
                  <p className="text-sm text-slate-500">
                    Premium AI underwriting platform
                  </p>
                </div>
              </Link>

              <div className="flex items-center gap-3">
                {userId ? (
                  <Link href="/dashboard">
                    <Button className="rounded-2xl px-5">Go to Dashboard</Button>
                  </Link>
                ) : (
                  <>
                    <Link href="/sign-up">
                      <Button className="rounded-2xl px-5">Register</Button>
                    </Link>
                    <Link href="/sign-in">
                      <Button variant="outline" className="rounded-2xl px-5">
                        Sign In
                      </Button>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </header>

          <section className="grid flex-1 gap-8 px-6 py-10 md:px-10 xl:grid-cols-[minmax(0,1.1fr)_420px] xl:items-center">
            <div className="space-y-8">
              <div className="space-y-5">
                <span className="section-label">Fintech AI Underwriting</span>
                <h1 className="max-w-4xl text-5xl font-semibold tracking-tight text-slate-950 md:text-6xl">
                  Faster lending decisions with explainable AI, structured evidence, and premium operational control.
                </h1>
                <p className="max-w-2xl text-lg leading-8 text-slate-600">
                  Underlytics helps applicants submit loan requests, upload supporting
                  documents, and move through a planner + worker underwriting flow that
                  stays auditable from intake to final decision.
                </p>
              </div>

              <ActionButtons userId={userId} />

              <div className="grid gap-4 sm:grid-cols-3">
                {metrics.map((metric) => (
                  <div
                    key={metric.label}
                    className="rounded-[24px] border border-slate-200/80 bg-white/84 p-5 shadow-sm"
                  >
                    <p className="text-3xl font-semibold tracking-tight text-slate-950">
                      {metric.value}
                    </p>
                    <p className="mt-2 text-sm leading-6 text-slate-500">
                      {metric.label}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-5">
              <div className="overflow-hidden rounded-[32px] border border-slate-200/80 bg-slate-950 text-white shadow-[0_32px_80px_-48px_rgba(15,23,42,0.95)]">
                <div className="grid-pattern border-b border-white/10 px-6 py-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm text-white/70">Live underwriting workspace</p>
                      <h2 className="mt-1 font-heading text-2xl font-semibold">
                        Decision intelligence at a glance
                      </h2>
                    </div>
                    <StatusBadge tone="green">approved</StatusBadge>
                  </div>
                </div>

                <div className="space-y-5 px-6 py-6">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-[24px] border border-white/10 bg-white/6 p-5">
                      <p className="text-sm text-white/65">Risk assessment</p>
                      <p className="mt-3 text-3xl font-semibold">82%</p>
                      <p className="mt-2 text-sm text-white/70">
                        Confidence-backed decisioning from structured worker outputs.
                      </p>
                    </div>
                    <div className="rounded-[24px] border border-cyan-400/20 bg-cyan-400/10 p-5">
                      <p className="text-sm text-cyan-100/80">Planner status</p>
                      <p className="mt-3 text-xl font-semibold text-white">
                        Workers completed
                      </p>
                      <p className="mt-2 text-sm text-cyan-50/80">
                        Document, policy, risk, fraud, and summary steps aligned.
                      </p>
                    </div>
                  </div>

                  <div className="rounded-[24px] border border-white/10 bg-white/6 p-5">
                    <div className="flex items-center gap-3">
                      <ChartColumnIncreasing className="size-5 text-cyan-300" />
                      <p className="font-medium text-white">
                        Explainable AI signals
                      </p>
                    </div>
                    <div className="mt-4 grid gap-3 sm:grid-cols-3">
                      <div className="rounded-2xl bg-white/5 p-4">
                        <p className="text-xs tracking-[0.18em] text-white/55 uppercase">
                          Score
                        </p>
                        <p className="mt-2 text-lg font-semibold">0.82</p>
                      </div>
                      <div className="rounded-2xl bg-white/5 p-4">
                        <p className="text-xs tracking-[0.18em] text-white/55 uppercase">
                          Confidence
                        </p>
                        <p className="mt-2 text-lg font-semibold">0.91</p>
                      </div>
                      <div className="rounded-2xl bg-white/5 p-4">
                        <p className="text-xs tracking-[0.18em] text-white/55 uppercase">
                          Flags
                        </p>
                        <p className="mt-2 text-lg font-semibold">1 active</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {userId ? (
                <AdminBootstrapPanel currentRole={actorRole ?? "applicant"} />
              ) : null}
            </div>
          </section>

          <section className="border-t border-slate-200/70 px-6 py-10 md:px-10">
            <div className="grid gap-10 lg:grid-cols-[0.8fr_1fr]">
              <div className="space-y-4">
                <span className="section-label">Why teams trust it</span>
                <h2 className="text-3xl font-semibold tracking-tight text-slate-950">
                  Built for modern fintech operations, not generic back-office workflows.
                </h2>
                <p className="text-base leading-7 text-slate-600">
                  Every screen is designed around clarity: what decision was made, why it
                  happened, what evidence supported it, and when a human should step in.
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {features.map((feature) => {
                  const Icon = feature.icon;

                  return (
                    <div
                      key={feature.title}
                      className="rounded-[28px] border border-slate-200/80 bg-slate-50/80 p-6"
                    >
                      <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-indigo-600 shadow-sm">
                        <Icon className="size-5" />
                      </div>
                      <h3 className="mt-5 text-xl font-semibold text-slate-950">
                        {feature.title}
                      </h3>
                      <p className="mt-3 text-sm leading-7 text-slate-600">
                        {feature.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="border-t border-slate-200/70 px-6 py-10 md:px-10">
            <div className="grid gap-8 lg:grid-cols-[1fr_0.85fr]">
              <div className="rounded-[32px] border border-slate-200/80 bg-white p-7 shadow-sm">
                <span className="section-label">How it works</span>
                <div className="mt-6 space-y-5">
                  {steps.map((step, index) => (
                    <div key={step} className="flex gap-4">
                      <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 font-semibold text-indigo-700">
                        {index + 1}
                      </div>
                      <p className="pt-1 text-sm leading-7 text-slate-600">{step}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[32px] border border-cyan-200/60 bg-gradient-to-br from-cyan-50 to-white p-7">
                <span className="section-label">Explainable AI</span>
                <h2 className="mt-5 text-3xl font-semibold tracking-tight text-slate-950">
                  Transparent outputs by design
                </h2>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  Underlytics keeps each agent on a strict JSON contract so risk, fraud,
                  document, and decision signals can be inspected instead of hidden.
                </p>

                <div className="mt-6 space-y-3 rounded-[28px] border border-cyan-200/70 bg-white/90 p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <BadgeCheck className="size-5 text-emerald-600" />
                      <p className="font-medium text-slate-900">Structured decision payload</p>
                    </div>
                    <StatusBadge tone="cyan">json</StatusBadge>
                  </div>

                  <pre className="overflow-x-auto rounded-[24px] bg-slate-950 p-4 text-xs leading-6 text-cyan-100">
{`{
  "score": 0.82,
  "confidence": 0.91,
  "decision": "approved",
  "flags": ["high_dti"],
  "reasoning": "Income supports the requested term."
}`}
                  </pre>
                </div>
              </div>
            </div>
          </section>

          <footer className="border-t border-slate-200/70 px-6 py-6 md:px-10">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="font-heading text-lg font-semibold text-slate-950">
                  Underlytics
                </p>
                <p className="text-sm text-slate-500">
                  Premium AI-powered underwriting for explainable lending operations.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-5 text-sm text-slate-500">
                <Link href="/privacy-policy" className="transition hover:text-slate-900">
                  Privacy Policy
                </Link>
                <Link href="/terms-of-service" className="transition hover:text-slate-900">
                  Terms of Service
                </Link>
                <Link href="/cookie-policy" className="transition hover:text-slate-900">
                  Cookie Policy
                </Link>
              </div>
            </div>
          </footer>
        </div>
      </section>
    </main>
  );
}

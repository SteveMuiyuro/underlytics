import Link from "next/link";
import {
  ArrowRight,
  ChartSpline,
  FileBadge2,
  FileStack,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { getApplications } from "@/lib/api/applications";
import { getApplicationStats } from "@/lib/api/application-stats";
import { getBackendActorHeaders } from "@/lib/api/server-actor";
import { formatCurrency, getApplicationStatusMeta } from "@/lib/underlytics-ui";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";

const statCards = [
  {
    key: "total",
    label: "Total applications",
    description: "All submitted applications across the workspace.",
    accent: "indigo",
  },
  {
    key: "in_progress",
    label: "In progress",
    description: "Cases currently moving through underwriting.",
    accent: "cyan",
  },
  {
    key: "approved",
    label: "Approved",
    description: "Applications cleared for successful funding outcomes.",
    accent: "green",
  },
  {
    key: "rejected",
    label: "Rejected",
    description: "Applications that did not meet current decision thresholds.",
    accent: "red",
  },
] as const;

export default async function DashboardPage() {
  const actorHeaders = await getBackendActorHeaders();
  const [stats, applications] = await Promise.all([
    getApplicationStats(actorHeaders),
    getApplications(actorHeaders),
  ]);

  const recentApplications = applications.slice(0, 5);

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Workspace Overview"
        title="Underwriting Command Center"
        description="A premium view of application throughput, active underwriting cases, and the latest decisions flowing through the platform."
        actions={
          <>
            <Link href="/new-application">
              <Button className="h-11 rounded-2xl px-5">
                New Application
                <ArrowRight className="size-4" />
              </Button>
            </Link>
            <Link href="/applications">
              <Button variant="outline" className="h-11 rounded-2xl px-5">
                View Applications
              </Button>
            </Link>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statCards.map((card) => {
          const value = stats[card.key];

          return (
            <Card key={card.key} className="page-surface h-full py-0">
              <CardHeader className="min-h-28 border-b border-slate-200/70 py-5">
                <CardTitle className="text-xs tracking-[0.14em] text-slate-500 uppercase">
                  {card.label}
                </CardTitle>
                <CardDescription>{card.description}</CardDescription>
              </CardHeader>
              <CardContent className="mt-auto flex min-h-24 flex-col items-center justify-end gap-3 py-5 text-center">
                <p className="text-4xl font-semibold tracking-tight text-slate-950">
                  {value}
                </p>
                <StatusBadge
                  tone={card.accent}
                  className="justify-center px-2.5 text-[10px] tracking-[0.12em]"
                >
                  {card.label}
                </StatusBadge>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.8fr)]">
        <div className="space-y-6">
          <Card className="page-surface overflow-hidden py-0">
            <CardHeader className="border-b border-slate-200/70 py-6">
              <CardTitle>Recent Applications</CardTitle>
              <CardDescription>
                The newest cases entering or progressing through underwriting.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 py-6">
              {recentApplications.length > 0 ? (
                recentApplications.map((application) => {
                  const status = getApplicationStatusMeta(application.status);

                  return (
                    <div
                      key={application.id}
                      className="rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-5 transition hover:border-slate-300 hover:bg-white"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                        <div className="space-y-2">
                          <p className="text-lg font-semibold text-slate-950">
                            {application.application_number}
                          </p>
                          <div className="flex flex-wrap gap-2 text-sm text-slate-500">
                            <span>{formatCurrency(application.requested_amount)}</span>
                            <span>•</span>
                            <span>{application.employment_status ?? "Employment pending"}</span>
                            <span>•</span>
                            <span>{application.bank_name ?? "Bank pending"}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                          <Link href={`/applications/${application.application_number}`}>
                            <Button variant="outline" className="rounded-2xl">
                              Open Case
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="rounded-[24px] border border-dashed border-slate-200 bg-slate-50/60 p-10 text-center text-sm text-slate-500">
                  No applications available yet.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="overflow-hidden rounded-[32px] border border-slate-200/80 bg-slate-950 py-0 text-white shadow-[0_32px_80px_-48px_rgba(15,23,42,0.9)]">
            <CardHeader className="border-b border-white/10 py-6">
              <CardTitle className="text-white">AI Activity</CardTitle>
              <CardDescription className="text-white/65">
                A quick read on the underwriting system’s current operating mode.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 py-6">
              <div className="rounded-[24px] border border-white/10 bg-white/6 p-5">
                <div className="flex items-center gap-3">
                  <Sparkles className="size-5 text-cyan-300" />
                  <p className="font-medium">Planner orchestration ready</p>
                </div>
                <p className="mt-3 text-sm leading-7 text-white/72">
                  The workspace is prepared for document analysis, policy retrieval,
                  risk scoring, fraud verification, and decision summary aggregation.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="flex min-h-32 flex-col rounded-[20px] bg-white/6 p-4 text-center">
                  <p className="text-xs tracking-[0.14em] text-white/60 uppercase">
                    Active queue
                  </p>
                  <div className="mt-auto flex flex-col items-center justify-end gap-2">
                    <p className="text-2xl font-semibold">{stats.in_progress}</p>
                  </div>
                </div>
                <div className="flex min-h-32 flex-col rounded-[20px] bg-white/6 p-4 text-center">
                  <p className="text-xs tracking-[0.14em] text-white/60 uppercase">
                    Completed decisions
                  </p>
                  <div className="mt-auto flex flex-col items-center justify-end gap-2">
                    <p className="text-2xl font-semibold">
                      {stats.approved + stats.rejected}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="page-surface py-0">
            <CardHeader className="border-b border-slate-200/70 py-6">
              <CardTitle>Operational Focus</CardTitle>
              <CardDescription>
                Priority areas surfaced from current application volume.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 py-6">
              <div className="flex gap-4 rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-4">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-700">
                  <FileStack className="size-5" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">Application throughput</p>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    {stats.total} total applications currently visible in the workspace.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-4">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-cyan-50 text-cyan-700">
                  <ChartSpline className="size-5" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">Underwriting flow</p>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    {stats.in_progress} case(s) are still moving through worker execution.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-4">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
                  <ShieldCheck className="size-5" />
                </div>
                <div>
                  <p className="font-medium text-slate-900">Manual review readiness</p>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Manual review workflows remain available for escalated decisions and reviewer intervention.
                  </p>
                </div>
              </div>

              <Link href="/applications">
                <Button variant="outline" className="w-full rounded-2xl">
                  <FileBadge2 className="size-4" />
                  Open Applications
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}

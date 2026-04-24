"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bot,
  CheckCircle2,
  LoaderCircle,
  Sparkles,
  Workflow,
  XCircle,
  type LucideIcon,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiWorkflowStatus } from "@/lib/types/api-workflow-status";
import { cn } from "@/lib/utils";

interface ApplicationProcessingScreenProps {
  applicationNumber: string;
  initialStatus: ApiWorkflowStatus;
}

const MIN_VISIBLE_DELAY_MS = 1800;
const POLL_INTERVAL_MS = 2500;

const AGENT_ICONS: Record<string, LucideIcon> = {
  planner: Workflow,
  document_analysis: Bot,
  policy_retrieval: Bot,
  risk_assessment: Bot,
  fraud_verification: Bot,
  decision_summary: Sparkles,
};

const STATUS_META = {
  pending: {
    badgeTone: "neutral" as const,
    badgeLabel: "Pending",
    panelClassName: "border-slate-200/80 bg-slate-50/80",
    icon: LoaderCircle,
    iconClassName: "text-slate-400",
  },
  running: {
    badgeTone: "cyan" as const,
    badgeLabel: "Running",
    panelClassName: "border-cyan-200/80 bg-cyan-50/70",
    icon: LoaderCircle,
    iconClassName: "animate-spin text-cyan-600",
  },
  completed: {
    badgeTone: "green" as const,
    badgeLabel: "Completed",
    panelClassName: "border-emerald-200/80 bg-emerald-50/70",
    icon: CheckCircle2,
    iconClassName: "text-emerald-600",
  },
  failed: {
    badgeTone: "red" as const,
    badgeLabel: "Failed",
    panelClassName: "border-rose-200/80 bg-rose-50/70",
    icon: XCircle,
    iconClassName: "text-rose-600",
  },
};

async function fetchWorkflowStatus(
  applicationNumber: string
): Promise<ApiWorkflowStatus> {
  const response = await fetch(`/api/applications/${applicationNumber}/workflow-status`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to refresh workflow status");
  }

  return response.json();
}

export default function ApplicationProcessingScreen({
  applicationNumber,
  initialStatus,
}: ApplicationProcessingScreenProps) {
  const router = useRouter();
  const mountedAtRef = useRef(0);
  const redirectTimeoutRef = useRef<number | null>(null);

  const [status, setStatus] = useState<ApiWorkflowStatus>(initialStatus);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const currentAgent = useMemo(
    () =>
      status.agents.find((agent) => agent.name === status.current_stage) ??
      status.agents[0],
    [status]
  );

  useEffect(() => {
    mountedAtRef.current = Date.now();
  }, []);

  useEffect(() => {
    if (status.status !== "processing") {
      return;
    }

    const intervalId = window.setInterval(async () => {
      try {
        setIsRefreshing(true);
        const nextStatus = await fetchWorkflowStatus(applicationNumber);
        setStatus(nextStatus);
        setFetchError(null);
      } catch (error) {
        setFetchError(
          error instanceof Error ? error.message : "Unable to refresh workflow status."
        );
      } finally {
        setIsRefreshing(false);
      }
    }, POLL_INTERVAL_MS);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [applicationNumber, status.status]);

  useEffect(() => {
    if (status.status !== "completed") {
      return;
    }

    const elapsed = mountedAtRef.current ? Date.now() - mountedAtRef.current : 0;
    const remainingDelay = Math.max(MIN_VISIBLE_DELAY_MS - elapsed, 0);

    redirectTimeoutRef.current = window.setTimeout(() => {
      router.replace(`/applications/${applicationNumber}`);
    }, remainingDelay);

    return () => {
      if (redirectTimeoutRef.current !== null) {
        window.clearTimeout(redirectTimeoutRef.current);
      }
    };
  }, [applicationNumber, router, status.status]);

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden rounded-[32px] border border-slate-200/80 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.12),transparent_34%),linear-gradient(180deg,#020617_0%,#0f172a_100%)] py-0 text-white shadow-[0_32px_80px_-48px_rgba(15,23,42,0.9)]">
        <CardHeader className="border-b border-white/10 bg-white/[0.02] py-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/15">
                  <Workflow className="size-5 text-cyan-300" />
                </div>
                <div>
                  <CardTitle className="text-white">Application Processing</CardTitle>
                  <p className="mt-1 text-sm text-white/65">
                    Planner and worker agents are processing application{" "}
                    {applicationNumber}.
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <StatusBadge tone={status.status === "failed" ? "red" : status.status === "completed" ? "green" : "cyan"}>
                  {status.status === "failed"
                    ? "Workflow Failed"
                    : status.status === "completed"
                      ? "Decision Ready"
                      : "Processing"}
                </StatusBadge>
                <StatusBadge tone="slate">{status.progress}% complete</StatusBadge>
                {isRefreshing ? <StatusBadge tone="neutral">Refreshing</StatusBadge> : null}
              </div>
            </div>

            <div className="w-full max-w-sm rounded-[24px] border border-white/10 bg-white/6 px-5 py-4">
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm text-white/65">Current stage</p>
                <p className="text-sm font-medium text-white">{currentAgent.label}</p>
              </div>
              <Progress
                value={status.progress}
                className="mt-4 bg-white/10"
                indicatorClassName="bg-cyan-300"
              />
              <p className="mt-3 text-sm leading-6 text-white/72">
                {currentAgent.snippet}
              </p>
            </div>
          </div>
        </CardHeader>
      </Card>

      {fetchError ? (
        <Alert className="border-rose-200 bg-rose-50/80 text-rose-950">
          <AlertTitle>Workflow updates are temporarily unavailable</AlertTitle>
          <AlertDescription>
            {fetchError}
          </AlertDescription>
        </Alert>
      ) : null}

      {status.status === "failed" ? (
        <Alert className="border-rose-200 bg-rose-50/80 text-rose-950">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2">
              <AlertTitle>Workflow processing failed</AlertTitle>
              <AlertDescription>
                The application detail page still has the latest saved state. You can
                review the case there and retry or investigate from the workflow history.
              </AlertDescription>
            </div>
            <Link href={`/applications/${applicationNumber}`}>
              <Button variant="outline" className="rounded-2xl">
                View Application Detail
              </Button>
            </Link>
          </div>
        </Alert>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        {status.agents.map((agent) => {
          const Icon = AGENT_ICONS[agent.name] ?? Bot;
          const statusMeta = STATUS_META[agent.status];
          const StatusIcon = statusMeta.icon;
          const isCurrent = status.current_stage === agent.name && status.status === "processing";

          return (
            <Card
              key={agent.name}
              className={cn(
                "rounded-[28px] border py-0 shadow-sm transition-colors",
                statusMeta.panelClassName,
                isCurrent ? "ring-1 ring-cyan-300/70" : undefined
              )}
            >
              <CardContent className="space-y-4 p-5">
                <div className="flex min-w-0 items-start gap-3">
                  <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-white text-indigo-600 shadow-sm">
                    <Icon className="size-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-slate-950">{agent.label}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      {agent.snippet}
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge tone={statusMeta.badgeTone}>
                    {statusMeta.badgeLabel}
                  </StatusBadge>
                  {isCurrent ? <StatusBadge tone="cyan">Active</StatusBadge> : null}
                  {agent.decision ? (
                    <StatusBadge tone="slate">{agent.decision.replaceAll("_", " ")}</StatusBadge>
                  ) : null}
                </div>

                <div className="rounded-[22px] border border-white/70 bg-white/80 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-950">
                    <StatusIcon className={cn("size-4", statusMeta.iconClassName)} />
                    <span>Agent activity</span>
                  </div>
                  {agent.reasoning ? (
                    <p className="mt-3 text-sm leading-7 text-slate-600">
                      {agent.reasoning}
                    </p>
                  ) : (
                    <div className="mt-3 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-4 w-full" />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {status.status === "completed" ? (
        <Alert className="border-emerald-200 bg-emerald-50/80 text-emerald-950">
          <AlertTitle>Decision ready</AlertTitle>
          <AlertDescription>
            The underwriting workflow has completed. Redirecting to the application
            detail page now.
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="flex justify-end">
        <Link href={`/applications/${applicationNumber}`}>
          <Button variant="outline" className="rounded-2xl">
            View Application Detail
          </Button>
        </Link>
      </div>
    </div>
  );
}

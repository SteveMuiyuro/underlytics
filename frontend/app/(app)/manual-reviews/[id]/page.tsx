import Link from "next/link";
import { notFound } from "next/navigation";
import { History, ShieldCheck } from "lucide-react";

import ReviewActionPanel from "@/components/manual-review/review-action-panel";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { getAgentOutputs } from "@/lib/api/agent-outputs";
import { getApplication } from "@/lib/api/applications";
import { getApplicationDocuments } from "@/lib/api/documents-list";
import { getManualReviewCase } from "@/lib/api/manual-review";
import { getBackendActor, getBackendActorHeaders } from "@/lib/api/server-actor";
import {
  formatAgentName,
  formatCurrency,
  formatDocumentType,
  formatPercent,
  getManualReviewStatusMeta,
  humanize,
  parseFlags,
} from "@/lib/underlytics-ui";

export default async function ManualReviewDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let reviewCase;
  let application;
  let documents;
  let outputs;
  let actor;

  try {
    const actorHeaders = await getBackendActorHeaders();
    actor = await getBackendActor();
    reviewCase = await getManualReviewCase(id, actorHeaders);
    application = await getApplication(reviewCase.application_number, actorHeaders);
    [documents, outputs] = await Promise.all([
      getApplicationDocuments(application.id, actorHeaders),
      getAgentOutputs(application.id, actorHeaders),
    ]);
  } catch {
    notFound();
  }

  const status = getManualReviewStatusMeta(reviewCase.status);

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Manual Review"
        title={`Case ${reviewCase.application_number}`}
        description="Reviewer decision workspace for escalated underwriting outcomes, supporting evidence, and final notes."
        actions={<StatusBadge tone={status.tone}>{status.label}</StatusBadge>}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.75fr)]">
          <div className="space-y-6">
            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Case Summary</CardTitle>
                <CardDescription>{reviewCase.reason}</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 py-6 sm:grid-cols-2">
                {[
                  ["Application", reviewCase.application_number],
                  ["Requested Amount", formatCurrency(reviewCase.requested_amount)],
                  ["Current Decision", humanize(reviewCase.application_status)],
                  ["Workflow Status", humanize(reviewCase.workflow_plan_status)],
                ].map(([label, value]) => (
                  <div
                    key={label}
                    className="rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-5"
                  >
                    <p className="text-sm text-slate-500">{label}</p>
                    <p className="mt-2 font-medium text-slate-950">{value}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Underwriting Evidence</CardTitle>
                <CardDescription>
                  Latest worker outputs that contributed to this escalation.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 py-6">
                {outputs.map((output) => {
                  const flags = parseFlags(output.flags);

                  return (
                    <div
                      key={output.id}
                      className="rounded-[28px] border border-slate-200/80 bg-slate-50/80 p-5"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                          <p className="font-medium text-slate-950">
                            {formatAgentName(output.agent_name)}
                          </p>
                          <p className="mt-2 text-sm leading-7 text-slate-600">
                            {output.reasoning || "No reasoning captured."}
                          </p>
                        </div>
                        <div className="grid min-w-52 gap-3 sm:grid-cols-2">
                          <div className="rounded-[20px] border border-slate-200/80 bg-white p-4">
                            <p className="text-xs tracking-[0.18em] text-slate-400 uppercase">
                              Score
                            </p>
                            <p className="mt-2 text-lg font-semibold text-slate-950">
                              {formatPercent(output.score)}
                            </p>
                          </div>
                          <div className="rounded-[20px] border border-slate-200/80 bg-white p-4">
                            <p className="text-xs tracking-[0.18em] text-slate-400 uppercase">
                              Confidence
                            </p>
                            <p className="mt-2 text-lg font-semibold text-slate-950">
                              {formatPercent(output.confidence)}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 flex flex-wrap gap-2">
                        {flags.length > 0 ? (
                          flags.map((flag) => (
                            <StatusBadge key={flag} tone="amber">
                              {humanize(flag)}
                            </StatusBadge>
                          ))
                        ) : (
                          <StatusBadge tone="green">no flags</StatusBadge>
                        )}
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Documents</CardTitle>
                <CardDescription>Files attached to the underlying application.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 py-6">
                {documents.length > 0 ? (
                  documents.map((document) => (
                    <div
                      key={document.id}
                      className="flex flex-col gap-3 rounded-[24px] border border-slate-200/80 bg-slate-50/80 px-5 py-4 md:flex-row md:items-center md:justify-between"
                    >
                      <div>
                        <p className="font-medium text-slate-950">
                          {formatDocumentType(document.document_type)}
                        </p>
                        <p className="mt-1 text-sm text-slate-500">{document.file_name}</p>
                      </div>
                      <StatusBadge tone="cyan">{humanize(document.upload_status)}</StatusBadge>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No documents uploaded yet.</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Reviewer Actions</CardTitle>
                <CardDescription>
                  Claim the case or record the final reviewer decision.
                </CardDescription>
              </CardHeader>
              <CardContent className="py-6">
                <ReviewActionPanel
                  caseId={reviewCase.id}
                  caseStatus={reviewCase.status}
                  isAssignedToCurrentReviewer={
                    reviewCase.assigned_reviewer_user_id === actor.backendUserId
                  }
                />
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <div className="flex items-center gap-3">
                  <History className="size-5 text-slate-500" />
                  <div>
                    <CardTitle>Review History</CardTitle>
                    <CardDescription>Chronological reviewer actions and notes.</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4 py-6">
                {reviewCase.actions.length > 0 ? (
                  reviewCase.actions.map((action) => (
                    <div
                      key={action.id}
                      className="rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-5"
                    >
                      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <p className="font-medium text-slate-950">
                          {humanize(action.action)}
                        </p>
                        <p className="text-xs text-slate-500">
                          {new Date(action.created_at).toLocaleString()}
                        </p>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-slate-600">
                        {action.note}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No reviewer actions yet.</p>
                )}
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="size-5 text-slate-500" />
                  <div>
                    <CardTitle>Application File</CardTitle>
                    <CardDescription>Open the full applicant workspace.</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="py-6">
                <Link href={`/applications/${reviewCase.application_number}`}>
                  <StatusBadge tone="indigo" className="cursor-pointer">
                    Open Full Application
                  </StatusBadge>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
    </section>
  );
}

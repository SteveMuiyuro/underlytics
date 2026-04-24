import { notFound } from "next/navigation";
import {
  Activity,
  ArrowUpRight,
  Bot,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  Clock3,
  FileText,
  FolderOpen,
  Mail,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Workflow,
  type LucideIcon,
} from "lucide-react";

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
import { getBackendActorHeaders } from "@/lib/api/server-actor";
import { getAgentRuns, getUnderwritingJob } from "@/lib/api/workflow";
import {
  formatAgentName,
  formatCurrency,
  formatDocumentType,
  formatFileSize,
  formatPercent,
  formatWorkflowStep,
  getApplicationStatusMeta,
  getWorkflowStatusMeta,
  humanize,
  parseFlags,
} from "@/lib/underlytics-ui";

const baseTimeline = [
  "Application submitted",
  "Documents uploaded",
  "Planner workflow started",
  "Worker evaluations completed",
  "Decision summarized",
];

export default async function ApplicationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let application;
  let documents;
  let job;
  let agentRuns;
  let agentOutputs;

  try {
    const actorHeaders = await getBackendActorHeaders();
    application = await getApplication(id, actorHeaders);
    documents = await getApplicationDocuments(application.id, actorHeaders);
    job = await getUnderwritingJob(application.application_number, actorHeaders);
    agentRuns = job ? await getAgentRuns(job.id, actorHeaders) : [];
    agentOutputs = await getAgentOutputs(application.id, actorHeaders);
  } catch {
    notFound();
  }

  const outputMap = new Map(agentOutputs.map((output) => [output.agent_name, output]));
  const decisionOutput =
    outputMap.get("decision_summary") ??
    agentOutputs.find((output) => output.decision || output.reasoning) ??
    null;

  const decisionFlags = parseFlags(decisionOutput?.flags ?? null);
  const applicationStatus = getApplicationStatusMeta(application.status);
  const decisionBadge = decisionOutput?.decision
    ? getApplicationStatusMeta(decisionOutput.decision)
    : applicationStatus;
  const plannerStatus = getWorkflowStatusMeta(job?.status ?? "pending");
  const applicationDetailItems: { label: string; value: string; Icon: LucideIcon }[] = [
    {
      label: "Employment Status",
      value: application.employment_status || "N/A",
      Icon: BriefcaseBusiness,
    },
    {
      label: "Employer Name",
      value: application.employer_name || "N/A",
      Icon: BriefcaseBusiness,
    },
    {
      label: "Bank Name",
      value: application.bank_name || "N/A",
      Icon: FolderOpen,
    },
    {
      label: "Account Type",
      value: application.account_type || "N/A",
      Icon: FolderOpen,
    },
    {
      label: "Monthly Income",
      value: formatCurrency(application.monthly_income),
      Icon: Activity,
    },
    {
      label: "Monthly Expenses",
      value: formatCurrency(application.monthly_expenses),
      Icon: Activity,
    },
    {
      label: "Existing Obligations",
      value: formatCurrency(application.existing_loan_obligations),
      Icon: TriangleAlert,
    },
    {
      label: "Loan Purpose",
      value: application.loan_purpose || "Not provided",
      Icon: FileText,
    },
  ];
  const completedRuns = agentRuns.filter((run) => run.status === "completed").length;
  const timeline = [
    baseTimeline[0],
    documents.length > 0 ? `${documents.length} document(s) uploaded` : baseTimeline[1],
    job ? `Planner job ${job.status}` : baseTimeline[2],
    `${completedRuns} of ${agentRuns.length || 0} worker runs completed`,
    decisionOutput?.decision
      ? `Decision summary: ${humanize(decisionOutput.decision)}`
      : baseTimeline[4],
  ];

  return (
    <section className="space-y-6">
        <PageHeader
          eyebrow="Application Workspace"
          title={`Application ${application.application_number}`}
          description="Review decision intelligence, planner execution, worker evidence, and supporting documents in one underwriting workspace."
          actions={<StatusBadge tone={applicationStatus.tone}>{applicationStatus.label}</StatusBadge>}
        />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.75fr)]">
          <div className="space-y-6">
            <Card className="overflow-hidden rounded-[32px] border border-slate-200/80 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.14),transparent_34%),linear-gradient(180deg,#020617_0%,#0f172a_100%)] py-0 text-white shadow-[0_32px_80px_-48px_rgba(15,23,42,0.9)]">
              <CardHeader className="border-b border-white/10 bg-white/[0.02] py-6">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className="flex size-11 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/15">
                        <Sparkles className="size-5 text-cyan-300" />
                      </div>
                      <div>
                        <CardTitle className="text-white">Decision Summary</CardTitle>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <StatusBadge tone={decisionBadge.tone}>{decisionBadge.label}</StatusBadge>
                    </div>
                    <CardDescription className="max-w-2xl text-white/65">
                      Final underwriting signal with score, confidence, reasoning, and flags.
                    </CardDescription>
                  </div>

                  <div className="rounded-[24px] border border-white/10 bg-white/6 px-5 py-4 lg:min-w-[240px]">
                    <p className="text-sm text-white/65">Requested amount</p>
                    <p className="mt-2 text-3xl font-semibold tracking-tight text-white">
                      {formatCurrency(application.requested_amount)}
                    </p>
                    <p className="mt-1 text-sm text-white/65">
                      {application.requested_term_months} month term
                    </p>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-5 py-6">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-[24px] border border-white/10 bg-white/6 p-5">
                    <p className="text-xs tracking-[0.18em] text-white/55 uppercase">Score</p>
                    <p className="mt-3 text-3xl font-semibold">
                      {formatPercent(decisionOutput?.score)}
                    </p>
                  </div>
                  <div className="rounded-[24px] border border-white/10 bg-white/6 p-5">
                    <p className="text-xs tracking-[0.18em] text-white/55 uppercase">Confidence</p>
                    <p className="mt-3 text-3xl font-semibold">
                      {formatPercent(decisionOutput?.confidence)}
                    </p>
                  </div>
                  <div className="rounded-[24px] border border-white/10 bg-white/6 p-5">
                    <p className="text-xs tracking-[0.18em] text-white/55 uppercase">Decision</p>
                    <p className="mt-3 text-3xl font-semibold">
                      {decisionOutput?.decision ? humanize(decisionOutput.decision) : applicationStatus.label}
                    </p>
                  </div>
                </div>

                <div className="rounded-[28px] border border-white/10 bg-white/6 p-5">
                  <p className="text-xs tracking-[0.18em] text-white/55 uppercase">Reasoning</p>
                  <p className="mt-3 text-sm leading-7 text-white/78">
                    {decisionOutput?.reasoning || "No decision reasoning is available yet for this application."}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {decisionFlags.length > 0 ? (
                    decisionFlags.map((flag) => (
                      <StatusBadge key={flag} tone="amber">
                        {humanize(flag)}
                      </StatusBadge>
                    ))
                  ) : (
                    <StatusBadge tone="green">no active flags</StatusBadge>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <CardTitle>Planner Workflow</CardTitle>
                    <CardDescription>
                      The central coordinator and its worker executions for this case.
                    </CardDescription>
                  </div>
                  <StatusBadge tone={plannerStatus.tone}>{plannerStatus.label}</StatusBadge>
                </div>
              </CardHeader>

              <CardContent className="space-y-5 py-6">
                {job ? (
                  <>
                    <div className="rounded-[28px] border border-slate-200/80 bg-slate-950 p-6 text-white">
                      <div className="space-y-5">
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                          <div className="space-y-3">
                            <div className="flex items-center gap-3">
                              <div className="flex size-11 items-center justify-center rounded-2xl bg-white/10">
                                <Workflow className="size-5 text-cyan-300" />
                              </div>
                              <div>
                                <p className="text-lg font-semibold">Planner Job</p>
                                <p className="text-sm text-white/65">
                                  Current step: {formatWorkflowStep(job.current_step)}
                                </p>
                              </div>
                            </div>
                          </div>

                          <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white/72">
                            Planner coordination is tracking each worker run independently and
                            updating the case timeline in real time.
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                          <StatusBadge tone={plannerStatus.tone}>{plannerStatus.label}</StatusBadge>
                          <StatusBadge tone="cyan">{completedRuns} completed workers</StatusBadge>
                        </div>

                        <div className="grid gap-3 md:grid-cols-3">
                          <div className="rounded-2xl bg-white/6 px-4 py-4">
                            <p className="text-xs tracking-[0.18em] text-white/55 uppercase">
                              Retries
                            </p>
                            <p className="mt-2 text-lg font-semibold">{job.retry_count}</p>
                          </div>
                          <div className="rounded-2xl bg-white/6 px-4 py-4">
                            <p className="text-xs tracking-[0.18em] text-white/55 uppercase">
                              Started
                            </p>
                            <p className="mt-2 text-sm leading-6 font-medium text-white/80">
                              {job.started_at
                                ? new Date(job.started_at).toLocaleString()
                                : "Pending"}
                            </p>
                          </div>
                          <div className="rounded-2xl bg-white/6 px-4 py-4">
                            <p className="text-xs tracking-[0.18em] text-white/55 uppercase">
                              Updated
                            </p>
                            <p className="mt-2 text-sm leading-6 font-medium text-white/80">
                              {new Date(job.updated_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="grid gap-4 xl:grid-cols-2">
                      {agentRuns.map((run) => {
                        const output = outputMap.get(run.agent_name);
                        const flags = parseFlags(output?.flags ?? null);
                        const workflowStatus = getWorkflowStatusMeta(run.status);

                        return (
                          <div
                            key={run.id}
                            className="rounded-[28px] border border-slate-200/80 bg-slate-50/80 p-5"
                          >
                            <div className="flex flex-col gap-4">
                              <div className="flex min-w-0 items-start gap-3">
                                <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-indigo-600 shadow-sm">
                                  <Bot className="size-5" />
                                </div>
                                <div className="min-w-0">
                                  <p className="font-medium text-slate-950">
                                    {formatAgentName(run.agent_name)}
                                  </p>
                                  <p className="mt-1 text-sm text-slate-500">
                                    Retries: {run.retry_count}
                                  </p>
                                </div>
                              </div>

                              <div className="flex flex-wrap items-center gap-2">
                                <StatusBadge
                                  tone={workflowStatus.tone}
                                  className="w-fit shrink-0"
                                >
                                  {workflowStatus.label}
                                </StatusBadge>
                              </div>

                              <div className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
                                <div className="flex min-h-[102px] flex-col justify-between rounded-[20px] border border-slate-200/80 bg-white p-4">
                                  <p className="text-xs tracking-[0.18em] text-slate-400 uppercase">
                                    Score
                                  </p>
                                  <p className="mt-2 text-lg font-semibold text-slate-950">
                                    {formatPercent(output?.score)}
                                  </p>
                                </div>
                                <div className="flex min-h-[102px] flex-col justify-between rounded-[20px] border border-slate-200/80 bg-white p-4">
                                  <p className="text-xs tracking-[0.18em] text-slate-400 uppercase">
                                    Confidence
                                  </p>
                                  <p className="mt-2 text-lg font-semibold text-slate-950">
                                    {formatPercent(output?.confidence)}
                                  </p>
                                </div>
                                <div className="flex min-h-[102px] flex-col justify-between rounded-[20px] border border-slate-200/80 bg-white p-4 sm:col-span-2 2xl:col-span-1">
                                  <p className="text-xs tracking-[0.18em] text-slate-400 uppercase">
                                    Decision
                                  </p>
                                  <p className="mt-2 text-base leading-6 font-semibold text-slate-950 sm:text-lg">
                                    {output?.decision ? humanize(output.decision) : "Pending"}
                                  </p>
                                </div>
                              </div>

                              <div className="rounded-[22px] border border-slate-200/80 bg-white p-4">
                                <p className="text-xs tracking-[0.18em] text-slate-400 uppercase">
                                  Reasoning
                                </p>
                                <p className="mt-3 text-sm leading-7 text-slate-600">
                                  {output?.reasoning || "No reasoning available yet."}
                                </p>
                              </div>

                              <div className="flex flex-wrap gap-2">
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

                              {run.error_message ? (
                                <div className="rounded-[20px] border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                                  Error: {run.error_message}
                                </div>
                              ) : null}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </>
                ) : (
                  <div className="rounded-[28px] border border-dashed border-slate-200 bg-slate-50/60 p-8 text-center text-sm text-slate-500">
                    No workflow job exists for this application yet.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Application Details</CardTitle>
                <CardDescription>
                  Core applicant, employment, and banking information supplied with the request.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 py-6 sm:grid-cols-2">
                {applicationDetailItems.map(({ label, value, Icon }) => {
                  return (
                  <div
                    key={label}
                    className="rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-5"
                  >
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Icon className="size-4" />
                      <p>{label}</p>
                    </div>
                    <p className="mt-3 text-base font-medium leading-7 text-slate-950">
                      {value}
                    </p>
                  </div>
                  );
                })}
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Submitted Documents</CardTitle>
                <CardDescription>
                  Review the files that were submitted with this application.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5 py-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-950">
                        Document Inventory
                      </h3>
                      <p className="text-sm text-slate-500">
                        Files already available to workers and reviewers.
                      </p>
                    </div>
                    <StatusBadge tone="cyan">{documents.length} files</StatusBadge>
                  </div>

                  {documents.length > 0 ? (
                    <div className="grid gap-4">
                      {documents.map((document) => (
                        <div
                          key={document.id}
                          className="rounded-[28px] border border-slate-200/80 bg-slate-50/80 p-5"
                        >
                          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                            <div className="flex gap-4">
                              <div className="flex size-12 items-center justify-center rounded-2xl bg-white text-indigo-600 shadow-sm">
                                <FileText className="size-5" />
                              </div>
                              <div>
                                <p className="font-medium text-slate-950">
                                  {formatDocumentType(document.document_type)}
                                </p>
                                <p className="mt-1 text-sm text-slate-500">
                                  {document.file_name}
                                </p>
                              </div>
                            </div>

                            <StatusBadge tone="cyan">{humanize(document.upload_status)}</StatusBadge>
                          </div>

                          <div className="mt-4 grid gap-3 text-sm text-slate-500 sm:grid-cols-3">
                            <div className="rounded-[20px] border border-slate-200/80 bg-white px-4 py-3">
                              Type: {document.mime_type}
                            </div>
                            <div className="rounded-[20px] border border-slate-200/80 bg-white px-4 py-3">
                              Size: {formatFileSize(document.file_size_bytes)}
                            </div>
                            <div className="rounded-[20px] border border-slate-200/80 bg-white px-4 py-3">
                              Uploaded: {new Date(document.uploaded_at).toLocaleString()}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-[28px] border border-dashed border-slate-200 bg-slate-50/60 p-8 text-center text-sm text-slate-500">
                      No documents uploaded yet.
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Case Snapshot</CardTitle>
                <CardDescription>
                  A concise summary for portfolio or reviewer context.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 py-6">
                <div className="rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-5">
                  <p className="text-sm text-slate-500">Application number</p>
                  <p className="mt-2 text-xl font-semibold text-slate-950">
                    {application.application_number}
                  </p>
                </div>
                <div className="rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-5">
                  <p className="text-sm text-slate-500">Requested amount</p>
                  <p className="mt-2 text-xl font-semibold text-slate-950">
                    {formatCurrency(application.requested_amount)}
                  </p>
                </div>
                <div className="rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-5">
                  <p className="text-sm text-slate-500">Current status</p>
                  <div className="mt-3">
                    <StatusBadge tone={applicationStatus.tone}>
                      {applicationStatus.label}
                    </StatusBadge>
                  </div>
                </div>
                <div className="rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-5">
                  <p className="text-sm text-slate-500">Planner status</p>
                  <div className="mt-3">
                    <StatusBadge tone={plannerStatus.tone}>{plannerStatus.label}</StatusBadge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Workflow Timeline</CardTitle>
                <CardDescription>
                  Key case milestones across submission and automated review.
                </CardDescription>
              </CardHeader>
              <CardContent className="py-6">
                <ol className="space-y-4">
                  {timeline.map((step, index) => (
                    <li key={step} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="flex size-9 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-700">
                          {index < completedRuns + 1 ? (
                            <CheckCircle2 className="size-4" />
                          ) : (
                            <Clock3 className="size-4" />
                          )}
                        </div>
                        {index < timeline.length - 1 ? (
                          <div className="mt-2 h-full w-px bg-slate-200" />
                        ) : null}
                      </div>
                      <p className="pt-1 text-sm leading-7 text-slate-600">{step}</p>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>

            <Card className="page-surface py-0">
              <CardHeader className="border-b border-slate-200/70 py-6">
                <CardTitle>Communication Log</CardTitle>
                <CardDescription>
                  Outbound updates and key audit timestamps for this application.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 py-6">
                <div className="flex gap-4 rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-4">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-slate-700 shadow-sm">
                    <Mail className="size-5" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-950">Email status</p>
                    <p className="mt-1 text-sm text-slate-500">
                      Notification workflows are not connected yet.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-4">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-slate-700 shadow-sm">
                    <CalendarClock className="size-5" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-950">Submitted at</p>
                    <p className="mt-1 text-sm text-slate-500">
                      {application.submitted_at
                        ? new Date(application.submitted_at).toLocaleString()
                        : "Not submitted"}
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-4">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-slate-700 shadow-sm">
                    <ArrowUpRight className="size-5" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-950">Last updated</p>
                    <p className="mt-1 text-sm text-slate-500">
                      {new Date(application.updated_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                {job ? (
                  <div className="flex gap-4 rounded-[24px] border border-slate-200/80 bg-slate-50/80 p-4">
                    <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-slate-700 shadow-sm">
                      <ShieldCheck className="size-5" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-950">Workflow audit</p>
                      <p className="mt-1 text-sm text-slate-500">
                        Planner updated {new Date(job.updated_at).toLocaleString()}.
                      </p>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </div>
    </section>
  );
}

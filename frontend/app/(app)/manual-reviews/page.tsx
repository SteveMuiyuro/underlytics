import Link from "next/link";
import { ShieldAlert } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getBackendActor, getBackendActorHeaders } from "@/lib/api/server-actor";
import { getManualReviewCases } from "@/lib/api/manual-review";
import {
  formatCurrency,
  getManualReviewStatusMeta,
  humanize,
} from "@/lib/underlytics-ui";

export default async function ManualReviewsPage() {
  const actorHeaders = await getBackendActorHeaders();
  const actor = await getBackendActor();
  const cases = await getManualReviewCases(actorHeaders);
  const assignedCount = cases.filter(
    (reviewCase) => reviewCase.assigned_reviewer_user_id === actor.backendUserId
  ).length;
  const unassignedCount = cases.filter(
    (reviewCase) => !reviewCase.assigned_reviewer_user_id
  ).length;

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Manual Review"
        title="Escalation Queue"
        description="Monitor applications that need reviewer intervention, inspect the reason for escalation, and open the detailed review workspace."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="page-surface h-full py-0">
          <CardHeader className="min-h-28 border-b border-slate-200/70 py-5">
            <CardTitle className="text-xs tracking-[0.14em] uppercase">
              Open Cases
            </CardTitle>
            <CardDescription>Cases awaiting reviewer disposition.</CardDescription>
          </CardHeader>
          <CardContent className="mt-auto flex min-h-24 items-end justify-center py-5">
            <p className="text-3xl font-semibold tracking-tight text-slate-950">
              {cases.length}
            </p>
          </CardContent>
        </Card>

        <Card className="page-surface h-full py-0">
          <CardHeader className="min-h-28 border-b border-slate-200/70 py-5">
            <CardTitle className="text-xs tracking-[0.14em] uppercase">
              Assigned To You
            </CardTitle>
            <CardDescription>Your currently owned escalations.</CardDescription>
          </CardHeader>
          <CardContent className="mt-auto flex min-h-24 items-end justify-center py-5">
            <p className="text-3xl font-semibold tracking-tight text-slate-950">
              {assignedCount}
            </p>
          </CardContent>
        </Card>

        <Card className="page-surface h-full py-0">
          <CardHeader className="min-h-28 border-b border-slate-200/70 py-5">
            <CardTitle className="text-xs tracking-[0.14em] uppercase">
              Unassigned
            </CardTitle>
            <CardDescription>Ready for a reviewer to claim.</CardDescription>
          </CardHeader>
          <CardContent className="mt-auto flex min-h-24 items-end justify-center py-5">
            <p className="text-3xl font-semibold tracking-tight text-slate-950">
              {unassignedCount}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="page-surface overflow-hidden">
        <div className="border-b border-slate-200/70 px-6 py-5">
          <h2 className="text-lg font-semibold text-slate-950">Review Queue</h2>
          <p className="mt-1 text-sm text-slate-500">
            Escalated cases surfaced from automated underwriting outcomes.
          </p>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="border-slate-200/70">
              <TableHead className="px-6 py-4 text-slate-500">Case</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Application</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Amount</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Status</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Reason</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Owner</TableHead>
              <TableHead className="px-6 py-4 text-right text-slate-500">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {cases.length > 0 ? (
              cases.map((reviewCase) => {
                const status = getManualReviewStatusMeta(reviewCase.status);

                return (
                  <TableRow
                    key={reviewCase.id}
                    className="border-slate-200/70 hover:bg-slate-50/80"
                  >
                    <TableCell className="px-6 py-5">
                      <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                    </TableCell>
                    <TableCell className="px-6 py-5 font-medium text-slate-950">
                      {reviewCase.application_number}
                    </TableCell>
                    <TableCell className="px-6 py-5 text-slate-600">
                      {formatCurrency(reviewCase.requested_amount)}
                    </TableCell>
                    <TableCell className="px-6 py-5 text-slate-600">
                      {humanize(reviewCase.application_status)}
                    </TableCell>
                    <TableCell className="max-w-sm px-6 py-5 text-slate-600">
                      <span className="line-clamp-2">{reviewCase.reason}</span>
                    </TableCell>
                    <TableCell className="px-6 py-5 text-slate-600">
                      {reviewCase.assigned_reviewer_user_id === actor.backendUserId
                        ? "You"
                        : reviewCase.assigned_reviewer_user_id
                          ? "Assigned"
                          : "Unassigned"}
                    </TableCell>
                    <TableCell className="px-6 py-5 text-right">
                      <Link href={`/manual-reviews/${reviewCase.id}`}>
                        <StatusBadge tone="indigo" className="cursor-pointer">
                          Open Case
                        </StatusBadge>
                      </Link>
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={7} className="px-6 py-16 text-center">
                  <div className="mx-auto flex max-w-md flex-col items-center text-center">
                    <div className="flex size-14 items-center justify-center rounded-3xl bg-slate-100 text-slate-500">
                      <ShieldAlert className="size-6" />
                    </div>
                    <p className="mt-4 text-lg font-medium text-slate-900">
                      No open manual review cases
                    </p>
                    <p className="mt-2 text-sm leading-6 text-slate-500">
                      Escalated cases will appear here when underwriting routes them for reviewer action.
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}

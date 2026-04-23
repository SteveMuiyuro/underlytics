import Link from "next/link";
import { ArrowRight, FileSearch, PlusCircle } from "lucide-react";

import { getApplications } from "@/lib/api/applications";
import { getBackendActorHeaders } from "@/lib/api/server-actor";
import { formatCurrency, getApplicationStatusMeta } from "@/lib/underlytics-ui";
import { Button } from "@/components/ui/button";
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

export default async function ApplicationsPage() {
  const actorHeaders = await getBackendActorHeaders();
  const applications = await getApplications(actorHeaders);
  const inProgressCount = applications.filter((application) => application.status === "in_progress").length;
  const approvedCount = applications.filter((application) => application.status === "approved").length;

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Applications"
        title="Application Pipeline"
        description="A clean underwriting list view with decision status, amount context, and direct access to each application workspace."
        actions={
          <Link href="/new-application">
            <Button className="h-11 rounded-2xl px-5">
              <PlusCircle className="size-4" />
              New Application
            </Button>
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <div className="page-surface flex min-h-36 flex-col p-5">
          <p className="text-xs tracking-[0.14em] text-slate-500 uppercase">
            Total applications
          </p>
          <div className="mt-auto flex items-end justify-center pt-6">
            <p className="text-3xl font-semibold tracking-tight text-slate-950">
              {applications.length}
            </p>
          </div>
        </div>
        <div className="page-surface flex min-h-36 flex-col p-5">
          <p className="text-xs tracking-[0.14em] text-slate-500 uppercase">
            In progress
          </p>
          <div className="mt-auto flex items-end justify-center pt-6">
            <p className="text-3xl font-semibold tracking-tight text-slate-950">
              {inProgressCount}
            </p>
          </div>
        </div>
        <div className="page-surface flex min-h-36 flex-col p-5">
          <p className="text-xs tracking-[0.14em] text-slate-500 uppercase">
            Approved
          </p>
          <div className="mt-auto flex items-end justify-center pt-6">
            <p className="text-3xl font-semibold tracking-tight text-slate-950">
              {approvedCount}
            </p>
          </div>
        </div>
      </div>

      <div className="page-surface overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-slate-200/70 px-6 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Applications</h2>
            <p className="mt-1 text-sm text-slate-500">
              Review current underwriting status, employment context, and banking information.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge tone="indigo">{inProgressCount} in progress</StatusBadge>
            <StatusBadge tone="green">{approvedCount} approved</StatusBadge>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="border-slate-200/70">
              <TableHead className="px-6 py-4 text-slate-500">Application</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Amount</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Status</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Employment</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Bank</TableHead>
              <TableHead className="px-6 py-4 text-right text-slate-500">Action</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {applications.length > 0 ? (
              applications.map((application) => {
                const status = getApplicationStatusMeta(application.status);

                return (
                  <TableRow
                    key={application.id}
                    className="border-slate-200/70 hover:bg-slate-50/80"
                  >
                    <TableCell className="px-6 py-5">
                      <div>
                        <p className="font-medium text-slate-950">
                          {application.application_number}
                        </p>
                        <p className="mt-1 text-sm text-slate-500">
                          {application.requested_term_months} month term
                        </p>
                      </div>
                    </TableCell>
                    <TableCell className="px-6 py-5 font-medium text-slate-900">
                      {formatCurrency(application.requested_amount)}
                    </TableCell>
                    <TableCell className="px-6 py-5">
                      <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                    </TableCell>
                    <TableCell className="px-6 py-5 text-slate-600">
                      {application.employment_status ?? "N/A"}
                    </TableCell>
                    <TableCell className="px-6 py-5 text-slate-600">
                      {application.bank_name ?? "N/A"}
                    </TableCell>
                    <TableCell className="px-6 py-5 text-right">
                      <Link href={`/applications/${application.application_number}`}>
                        <Button variant="outline" className="rounded-2xl">
                          Open
                          <ArrowRight className="size-4" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={6} className="px-6 py-16 text-center">
                  <div className="mx-auto flex max-w-md flex-col items-center text-center">
                    <div className="flex size-14 items-center justify-center rounded-3xl bg-slate-100 text-slate-500">
                      <FileSearch className="size-6" />
                    </div>
                    <p className="mt-4 text-lg font-medium text-slate-900">
                      No applications found
                    </p>
                    <p className="mt-2 text-sm leading-6 text-slate-500">
                      Start a new application to populate the underwriting pipeline.
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

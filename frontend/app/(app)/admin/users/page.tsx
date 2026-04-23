import { notFound } from "next/navigation";

import UserRoleManager from "@/components/admin/user-role-manager";
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
import { getUsers } from "@/lib/api/users";
import { getRoleMeta } from "@/lib/underlytics-ui";

export default async function AdminUsersPage() {
  const actor = await getBackendActor();
  if (actor.role !== "admin") {
    notFound();
  }

  const actorHeaders = await getBackendActorHeaders();
  const users = await getUsers(actorHeaders);

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Administration"
        title="User Access Control"
        description="Manage applicant, reviewer, and admin permissions from a single premium operations view."
      />

      <div className="page-surface overflow-hidden">
        <div className="border-b border-slate-200/70 px-6 py-5">
          <h2 className="text-lg font-semibold text-slate-950">Users</h2>
          <p className="mt-1 text-sm text-slate-500">
            Role-aware access for underwriting, review, and platform administration.
          </p>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="border-slate-200/70">
              <TableHead className="px-6 py-4 text-slate-500">Name</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Email</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Current Role</TableHead>
              <TableHead className="px-6 py-4 text-slate-500">Phone</TableHead>
              <TableHead className="px-6 py-4 text-right text-slate-500">Access</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {users.length > 0 ? (
              users.map((user) => {
                const role = getRoleMeta(user.role);

                return (
                  <TableRow
                    key={user.id}
                    className="border-slate-200/70 hover:bg-slate-50/80"
                  >
                    <TableCell className="px-6 py-5 font-medium text-slate-950">
                      {user.full_name}
                    </TableCell>
                    <TableCell className="px-6 py-5 text-slate-600">
                      {user.email}
                    </TableCell>
                    <TableCell className="px-6 py-5">
                      <StatusBadge tone={role.tone}>{role.label}</StatusBadge>
                    </TableCell>
                    <TableCell className="px-6 py-5 text-slate-600">
                      {user.phone_number ?? "N/A"}
                    </TableCell>
                    <TableCell className="px-6 py-5 text-right">
                      <UserRoleManager userId={user.id} currentRole={user.role} />
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={5} className="px-6 py-16 text-center text-slate-500">
                  No users found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}

import { UserButton } from "@clerk/nextjs";

import { getBackendActor } from "@/lib/api/server-actor";

export default async function AppTopbar() {
  const actor = await getBackendActor();

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Welcome back</h1>
        <p className="text-sm text-slate-500">
          {actor.role === "admin"
            ? "Administer access control and oversee underwriting operations"
            : actor.role === "reviewer"
            ? "Review escalated underwriting cases and finalize decisions"
            : "Track applications and underwriting activity"}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
          {actor.role === "admin"
            ? "Admin"
            : actor.role === "reviewer"
              ? "Reviewer"
              : "Applicant"}
        </div>
        <UserButton />
      </div>
    </header>
  );
}

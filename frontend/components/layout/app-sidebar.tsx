import Link from "next/link";

import { getBackendActor } from "@/lib/api/server-actor";

export default async function AppSidebar() {
  const actor = await getBackendActor();
  const navItems =
    actor.role === "admin"
      ? [
          { label: "Dashboard", href: "/dashboard" },
          { label: "Applications", href: "/applications" },
          { label: "Manual Reviews", href: "/manual-reviews" },
          { label: "Admin Users", href: "/admin/users" },
        ]
      : actor.role === "reviewer"
      ? [
          { label: "Dashboard", href: "/dashboard" },
          { label: "Applications", href: "/applications" },
          { label: "Manual Reviews", href: "/manual-reviews" },
        ]
      : [
          { label: "Dashboard", href: "/dashboard" },
          { label: "New Application", href: "/new-application" },
          { label: "Applications", href: "/applications" },
        ];

  return (
    <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white px-5 py-6 lg:flex">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Underlytics
        </h2>
        <p className="mt-1 text-sm text-slate-500">Loan underwriting platform</p>
      </div>

      <nav className="mt-10 flex flex-col gap-2">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-xl px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-900"
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}

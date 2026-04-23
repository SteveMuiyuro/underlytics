"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import {
  ArrowRight,
  FileBadge2,
  FileText,
  LayoutDashboard,
  Menu,
  PlusCircle,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";

interface AppShellProps {
  role: string;
  children: React.ReactNode;
}

type NavItem = {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
};

function getNavItems(role: string): NavItem[] {
  if (role === "admin") {
    return [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Applications", href: "/applications", icon: FileText },
      { label: "Manual Reviews", href: "/manual-reviews", icon: ShieldCheck },
      { label: "Admin Users", href: "/admin/users", icon: Users },
    ];
  }

  if (role === "reviewer") {
    return [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Applications", href: "/applications", icon: FileText },
      { label: "Manual Reviews", href: "/manual-reviews", icon: ShieldCheck },
    ];
  }

  return [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "New Application", href: "/new-application", icon: PlusCircle },
    { label: "Applications", href: "/applications", icon: FileBadge2 },
  ];
}

function getPageMeta(pathname: string) {
  const cleanPath = pathname.split("?")[0];
  const segments = cleanPath.split("/").filter(Boolean);
  const lastSegment = segments.at(-1);

  if (!lastSegment) {
    return {
      title: "Workspace",
      description: "AI-assisted underwriting operations and application workflows.",
      breadcrumb: ["Workspace"],
    };
  }

  if (cleanPath === "/dashboard") {
    return {
      title: "Dashboard",
      description: "Live underwriting activity, portfolio progress, and next actions.",
      breadcrumb: ["Workspace", "Dashboard"],
    };
  }

  if (cleanPath === "/new-application") {
    return {
      title: "New Application",
      description: "Capture applicant details, financials, and evidence in one guided flow.",
      breadcrumb: ["Applications", "New Application"],
    };
  }

  if (cleanPath === "/applications") {
    return {
      title: "Applications",
      description: "Monitor underwriting decisions, processing status, and document completeness.",
      breadcrumb: ["Applications"],
    };
  }

  if (segments[0] === "applications" && segments[1]) {
    return {
      title: `Application ${segments[1]}`,
      description: "Decision intelligence, worker outputs, supporting documents, and workflow progress.",
      breadcrumb: ["Applications", segments[1]],
    };
  }

  if (cleanPath === "/manual-reviews") {
    return {
      title: "Manual Reviews",
      description: "Prioritize escalations, resolve exceptions, and record reviewer outcomes.",
      breadcrumb: ["Operations", "Manual Reviews"],
    };
  }

  if (segments[0] === "manual-reviews" && segments[1]) {
    return {
      title: "Manual Review Case",
      description: "Examine evidence, capture notes, and finalize reviewer action.",
      breadcrumb: ["Operations", "Manual Reviews", segments[1]],
    };
  }

  if (cleanPath === "/admin/users") {
    return {
      title: "User Access Control",
      description: "Manage underwriting permissions and role assignment across the workspace.",
      breadcrumb: ["Admin", "Users"],
    };
  }

  return {
    title: segments.map((segment) => segment.replaceAll("-", " ")).join(" / "),
    description: "Underlytics operational workspace.",
    breadcrumb: segments.map((segment) => segment.replaceAll("-", " ")),
  };
}

function NavLink({
  item,
  pathname,
  onNavigate,
}: {
  item: NavItem;
  pathname: string;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;
  const isActive =
    pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));

  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={cn(
        "group flex items-center justify-between rounded-2xl px-4 py-3.5 text-sm font-medium transition-all",
        isActive
          ? "bg-slate-950 text-white shadow-[0_20px_40px_-26px_rgba(15,23,42,0.65)]"
          : "text-slate-600 hover:bg-white hover:text-slate-900"
      )}
    >
      <span className="flex items-center gap-3">
        <span
          className={cn(
            "flex size-9 items-center justify-center rounded-2xl border transition-all",
            isActive
              ? "border-white/15 bg-white/10 text-white"
              : "border-slate-200 bg-slate-50 text-slate-500 group-hover:border-slate-300 group-hover:bg-slate-100 group-hover:text-slate-700"
          )}
        >
          <Icon className="size-4" />
        </span>
        {item.label}
      </span>

      <ArrowRight
        className={cn(
          "size-4 transition-transform",
          isActive ? "translate-x-0 text-white/80" : "-translate-x-1 opacity-0 group-hover:translate-x-0 group-hover:opacity-100"
        )}
      />
    </Link>
  );
}

export default function AppShell({ role, children }: AppShellProps) {
  const pathname = usePathname();
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const navItems = getNavItems(role);
  const pageMeta = getPageMeta(pathname);
  const tone = role === "admin" ? "slate" : role === "reviewer" ? "cyan" : "indigo";

  return (
    <div className="min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-[1600px] gap-6 px-4 py-4 md:px-6 xl:px-8">
        <aside className="glass-panel hidden h-[calc(100vh-2rem)] w-[292px] flex-col justify-between rounded-[32px] p-5 lg:flex">
          <div className="space-y-8">
            <div className="rounded-[28px] border border-slate-200/80 bg-gradient-to-br from-slate-950 via-indigo-950 to-cyan-900 p-5 text-white">
              <div className="flex items-center gap-3">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-white/12 ring-1 ring-white/15">
                  <Sparkles className="size-5" />
                </div>
                <div>
                  <p className="font-heading text-lg font-semibold">Underlytics</p>
                  <p className="text-sm text-white/70">AI underwriting workspace</p>
                </div>
              </div>
              <p className="mt-5 text-sm leading-6 text-white/78">
                Planner plus worker intelligence for explainable, auditable lending decisions.
              </p>
            </div>

            <div className="space-y-3">
              <p className="px-2 text-xs font-semibold tracking-[0.22em] text-slate-400 uppercase">
                Navigation
              </p>
              <nav className="space-y-2">
                {navItems.map((item) => (
                  <NavLink key={item.href} item={item} pathname={pathname} />
                ))}
              </nav>
            </div>
          </div>

          <div className="rounded-[28px] border border-slate-200/80 bg-slate-50/80 p-5">
            <StatusBadge tone={tone}>{role}</StatusBadge>
            <p className="mt-3 text-sm font-medium text-slate-900">Secure operational mode</p>
            <p className="mt-1 text-sm leading-6 text-slate-500">
              Audit-friendly workspace for applications, reviews, and access control.
            </p>
          </div>
        </aside>

        <div className="flex min-h-screen min-w-0 flex-1 flex-col gap-4">
          <header className="glass-panel rounded-[28px] px-5 py-4 md:px-6">
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon-sm"
                    className="lg:hidden"
                    onClick={() => setIsMobileNavOpen(true)}
                  >
                    <Menu className="size-4" />
                  </Button>

                  <div>
                    <div className="flex flex-wrap items-center gap-2 text-xs font-medium tracking-[0.18em] text-slate-400 uppercase">
                      {pageMeta.breadcrumb.map((item) => (
                        <span key={item}>{item}</span>
                      ))}
                    </div>
                    <h1 className="mt-1 font-heading text-xl font-semibold tracking-tight text-slate-950 md:text-2xl">
                      {pageMeta.title}
                    </h1>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <StatusBadge tone={tone}>{role}</StatusBadge>
                  <UserButton />
                </div>
              </div>

              <p className="max-w-3xl text-sm leading-6 text-slate-500">
                {pageMeta.description}
              </p>
            </div>
          </header>

          <main className="min-w-0 flex-1">{children}</main>
        </div>
      </div>

      {isMobileNavOpen ? (
        <div className="fixed inset-0 z-50 bg-slate-950/35 backdrop-blur-sm lg:hidden">
          <div className="h-full max-w-[320px] p-4">
            <div className="flex h-full flex-col rounded-[32px] border border-white/60 bg-white p-5 shadow-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-heading text-lg font-semibold text-slate-950">
                    Underlytics
                  </p>
                  <p className="text-sm text-slate-500">Navigation</p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="icon-sm"
                  onClick={() => setIsMobileNavOpen(false)}
                >
                  <X className="size-4" />
                </Button>
              </div>

              <nav className="mt-8 space-y-2">
                {navItems.map((item) => (
                  <NavLink
                    key={item.href}
                    item={item}
                    pathname={pathname}
                    onNavigate={() => setIsMobileNavOpen(false)}
                  />
                ))}
              </nav>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

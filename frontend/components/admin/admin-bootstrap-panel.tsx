"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

interface AdminBootstrapPanelProps {
  currentRole: string;
}

export default function AdminBootstrapPanel({
  currentRole,
}: AdminBootstrapPanelProps) {
  const router = useRouter();
  const [bootstrapSecret, setBootstrapSecret] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  if (currentRole === "admin") {
    return (
      <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-6 text-left">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-700">
          Admin Access Active
        </p>
        <h3 className="mt-3 text-2xl font-semibold text-slate-900">
          This account already has admin access
        </h3>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Use the in-app admin screen to manage reviewer and applicant roles.
        </p>
      </div>
    );
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    startTransition(async () => {
      try {
        const response = await fetch("/api/admin/bootstrap", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            bootstrap_secret: bootstrapSecret,
          }),
        });

        if (!response.ok) {
          const body = await response.json().catch(() => null);
          throw new Error(body?.detail || "Failed to register admin");
        }

        setBootstrapSecret("");
        setSuccess("Admin access granted. Refreshing your session view.");
        router.refresh();
      } catch (bootstrapError) {
        setError(
          bootstrapError instanceof Error
            ? bootstrapError.message
            : "Failed to register admin"
        );
      }
    });
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 text-left shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-700">
        Admin Bootstrap
      </p>
      <h3 className="mt-3 text-2xl font-semibold text-slate-900">
        Register this signed-in account as an admin
      </h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Enter the backend bootstrap secret once. After that, use the admin console
        to assign reviewer or applicant roles.
      </p>

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <div>
          <label
            htmlFor="admin-bootstrap-secret"
            className="mb-2 block text-sm font-medium text-slate-700"
          >
            Admin Bootstrap Secret
          </label>
          <input
            id="admin-bootstrap-secret"
            type="password"
            value={bootstrapSecret}
            onChange={(event) => setBootstrapSecret(event.target.value)}
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            placeholder="Paste bootstrap secret"
            autoComplete="off"
            disabled={isPending}
          />
        </div>

        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}

        {success ? (
          <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {success}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={isPending || !bootstrapSecret.trim()}
          className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isPending ? "Registering Admin..." : "Register Admin"}
        </button>
      </form>
    </div>
  );
}

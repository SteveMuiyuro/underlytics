"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";

interface UserRoleManagerProps {
  userId: string;
  currentRole: string;
}

const ROLE_OPTIONS = ["applicant", "reviewer", "admin"] as const;

export default function UserRoleManager({
  userId,
  currentRole,
}: UserRoleManagerProps) {
  const router = useRouter();
  const [role, setRole] = useState(currentRole);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    startTransition(async () => {
      try {
        const response = await fetch(`/api/admin/users/${userId}/role`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ role }),
        });

        if (!response.ok) {
          const body = await response.json().catch(() => null);
          throw new Error(body?.detail || "Failed to update role");
        }

        router.refresh();
      } catch (updateError) {
        setError(
          updateError instanceof Error ? updateError.message : "Failed to update role"
        );
      }
    });
  }

  return (
    <form onSubmit={onSubmit} className="space-y-2">
      <div className="flex items-center justify-end gap-2">
        <Select
          value={role}
          onValueChange={(value) => setRole(value)}
          disabled={isPending}
          className="min-w-36 rounded-2xl"
          options={ROLE_OPTIONS.map((option) => ({
            label: option,
            value: option,
          }))}
        />

        <Button
          type="submit"
          disabled={isPending || role === currentRole}
          className="rounded-2xl"
        >
          Save
        </Button>
      </div>

      {error ? (
        <p className="text-right text-xs text-red-600">{error}</p>
      ) : null}
    </form>
  );
}

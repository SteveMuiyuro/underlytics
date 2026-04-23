import AppShell from "@/components/layout/app-shell";
import { getBackendActor } from "@/lib/api/server-actor";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let role = "applicant";

  try {
    const actor = await getBackendActor();
    role = actor.role;
  } catch {
    role = "applicant";
  }

  return (
    <AppShell role={role}>{children}</AppShell>
  );
}

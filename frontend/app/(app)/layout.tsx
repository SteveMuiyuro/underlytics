import AppShell from "@/components/layout/app-shell";
import { getBackendActor } from "@/lib/api/server-actor";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const actor = await getBackendActor();

  return (
    <AppShell role={actor.role}>{children}</AppShell>
  );
}

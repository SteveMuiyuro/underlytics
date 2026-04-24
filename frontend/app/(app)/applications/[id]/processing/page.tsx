import { notFound } from "next/navigation";

import ApplicationProcessingScreen from "@/components/applications/application-processing-screen";
import { PageHeader } from "@/components/ui/page-header";
import { getApplication } from "@/lib/api/applications";
import { getBackendActorHeaders } from "@/lib/api/server-actor";
import { getWorkflowStatus } from "@/lib/api/workflow";

export default async function ApplicationProcessingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let application;
  let workflowStatus;

  try {
    const actorHeaders = await getBackendActorHeaders();
    [application, workflowStatus] = await Promise.all([
      getApplication(id, actorHeaders),
      getWorkflowStatus(id, actorHeaders),
    ]);
  } catch {
    notFound();
  }

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Application Workspace"
        title={`Processing ${application.application_number}`}
        description="The planner is coordinating independent underwriting agents before the final case view becomes available."
      />

      <ApplicationProcessingScreen
        applicationNumber={application.application_number}
        initialStatus={workflowStatus}
      />
    </section>
  );
}

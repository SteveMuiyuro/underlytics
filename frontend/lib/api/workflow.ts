import { ApiAgentRun, ApiUnderwritingJob } from "@/lib/types/api-workflow";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getUnderwritingJob(
  applicationNumber: string,
  headers?: HeadersInit
): Promise<ApiUnderwritingJob | null> {
  const response = await fetch(
    `${API_URL}/api/workflow/applications/${applicationNumber}/job`,
    {
      cache: "no-store",
      headers,
    }
  );

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to fetch underwriting job");
  }

  return response.json();
}

export async function getAgentRuns(
  jobId: string,
  headers?: HeadersInit
): Promise<ApiAgentRun[]> {
  const response = await fetch(`${API_URL}/api/workflow/jobs/${jobId}/agent-runs`, {
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch agent runs");
  }

  return response.json();
}

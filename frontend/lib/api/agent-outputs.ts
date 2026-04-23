import { ApiAgentOutput } from "@/lib/types/api-agent-output";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getAgentOutputs(
  applicationId: string,
  headers?: HeadersInit
): Promise<ApiAgentOutput[]> {
  const response = await fetch(
    `${API_URL}/api/agent-outputs/applications/${applicationId}`,
    {
      cache: "no-store",
      headers,
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch agent outputs");
  }

  return response.json();
}

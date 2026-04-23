import { ApiApplicationStats } from "@/lib/types/api-application-stats";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getApplicationStats(
  headers?: HeadersInit
): Promise<ApiApplicationStats> {
  const response = await fetch(`${API_URL}/api/applications/stats`, {
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch application stats");
  }

  return response.json();
}

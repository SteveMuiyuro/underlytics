import { ApiApplication } from "@/lib/types/api-application";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Get all applications
export async function getApplications(
  headers?: HeadersInit
): Promise<ApiApplication[]> {
  const response = await fetch(`${API_URL}/api/applications`, {
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch applications");
  }

  return response.json();
}

// Get a single application by application number
export async function getApplication(
  applicationNumber: string,
  headers?: HeadersInit
): Promise<ApiApplication> {
  const response = await fetch(
    `${API_URL}/api/applications/${applicationNumber}`,
    {
      cache: "no-store",
      headers,
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch application");
  }

  return response.json();
}

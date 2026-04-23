import { ApiDocument } from "@/lib/types/api-document";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getApplicationDocuments(
  applicationId: string,
  headers?: HeadersInit
): Promise<ApiDocument[]> {
  const response = await fetch(
    `${API_URL}/api/application-documents/${applicationId}`,
    {
      cache: "no-store",
      headers,
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch application documents");
  }

  return response.json();
}

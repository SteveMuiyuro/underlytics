import {
  ApiManualReviewCaseDetail,
  ApiManualReviewCaseSummary,
} from "@/lib/types/api-manual-review";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getManualReviewCases(
  headers?: HeadersInit,
  status: string = "open"
): Promise<ApiManualReviewCaseSummary[]> {
  const response = await fetch(
    `${API_URL}/api/manual-review/cases?status=${encodeURIComponent(status)}`,
    {
      cache: "no-store",
      headers,
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch manual review cases");
  }

  return response.json();
}

export async function getManualReviewCase(
  caseId: string,
  headers?: HeadersInit
): Promise<ApiManualReviewCaseDetail> {
  const response = await fetch(`${API_URL}/api/manual-review/cases/${caseId}`, {
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch manual review case");
  }

  return response.json();
}

export async function submitManualReviewAction(
  caseId: string,
  payload: {
    action: string;
    note?: string;
  }
): Promise<ApiManualReviewCaseDetail> {
  const response = await fetch(`/api/manual-review/cases/${caseId}/actions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(errorBody?.detail || "Failed to submit manual review action");
  }

  return response.json();
}

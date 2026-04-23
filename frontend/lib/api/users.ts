import { ApiUser } from "@/lib/types/api-user";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getApplicantUsers(headers?: HeadersInit): Promise<ApiUser[]> {
  const response = await fetch(`${API_URL}/api/users/applicants`, {
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch applicant users");
  }

  return response.json();
}

export async function getUsers(headers?: HeadersInit): Promise<ApiUser[]> {
  const response = await fetch(`${API_URL}/api/users`, {
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch users");
  }

  return response.json();
}

export async function syncUser(payload: {
  clerk_user_id: string;
  email: string;
  full_name: string;
  phone_number?: string | null;
  role?: string | null;
}, headers?: HeadersInit): Promise<ApiUser> {
  const response = await fetch(`${API_URL}/api/users/sync`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    throw new Error(errorBody?.detail || "Failed to sync user");
  }

  return response.json();
}

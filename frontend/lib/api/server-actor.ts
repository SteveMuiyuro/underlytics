import "server-only";

import { cache } from "react";

import { getServerAuth, getServerCurrentUser } from "@/lib/auth/server";
import { syncUser } from "@/lib/api/users";

export interface BackendActor {
  backendUserId: string;
  role: string;
}

export const getBackendAuthHeaders = cache(async (): Promise<HeadersInit> => {
  const { userId, getToken } = await getServerAuth();

  if (!userId) {
    throw new Error("Authenticated actor is required");
  }

  const token = await getToken();
  if (!token) {
    throw new Error("Clerk session token is unavailable for backend requests");
  }

  return {
    Authorization: `Bearer ${token}`,
  };
});

export const getBackendActor = cache(async (): Promise<BackendActor> => {
  const { userId } = await getServerAuth();
  const clerkUser = await getServerCurrentUser();
  const authHeaders = await getBackendAuthHeaders();

  if (!userId || !clerkUser) {
    throw new Error("Authenticated actor is required");
  }

  const primaryEmail =
    clerkUser.emailAddresses.find(
      (email) => email.id === clerkUser.primaryEmailAddressId
    )?.emailAddress ?? clerkUser.emailAddresses[0]?.emailAddress;

  if (!primaryEmail) {
    throw new Error("No email address is available for this account");
  }

  const fullName =
    [clerkUser.firstName, clerkUser.lastName].filter(Boolean).join(" ") ||
    clerkUser.username ||
    "Applicant";

  const backendUser = await syncUser({
    clerk_user_id: userId,
    email: primaryEmail,
    full_name: fullName,
    phone_number:
      clerkUser.phoneNumbers[0]?.phoneNumber ??
      (clerkUser.unsafeMetadata?.phone_number as string | undefined) ??
      null,
  }, authHeaders);

  return {
    backendUserId: backendUser.id,
    role: backendUser.role,
  };
});

export async function getBackendActorHeaders(): Promise<HeadersInit> {
  return getBackendAuthHeaders();
}

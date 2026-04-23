import "server-only";

import { auth as clerkAuth, currentUser as clerkCurrentUser } from "@clerk/nextjs/server";

const CLERK_SERVER_AUTH_DEBUG = process.env.CLERK_SERVER_AUTH_DEBUG === "true";

function logClerkServerFailure(helper: "auth" | "currentUser", error: unknown) {
  if (!CLERK_SERVER_AUTH_DEBUG) {
    return;
  }

  if (!(error instanceof Error)) {
    console.error(
      JSON.stringify({
        scope: "clerk-server-auth",
        helper,
        message: "Unknown error",
      })
    );
    return;
  }

  const errorWithDigest = error as Error & { digest?: string };

  console.error(
    JSON.stringify({
      scope: "clerk-server-auth",
      helper,
      message: error.message,
      digest: errorWithDigest.digest ?? null,
    })
  );
}

export async function getServerAuth() {
  try {
    return await clerkAuth();
  } catch (error) {
    logClerkServerFailure("auth", error);
    throw error;
  }
}

export async function getServerCurrentUser() {
  try {
    return await clerkCurrentUser();
  } catch (error) {
    logClerkServerFailure("currentUser", error);
    throw error;
  }
}

import type { NextRequest } from "next/server";
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const CLERK_MIDDLEWARE_DEBUG = process.env.CLERK_MIDDLEWARE_DEBUG === "true";

function decodeJwtAzp(token: string | undefined) {
  if (!token) {
    return null;
  }

  const payload = token.split(".")[1];
  if (!payload) {
    return null;
  }

  try {
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      "="
    );
    const decoded = JSON.parse(atob(padded)) as { azp?: unknown };

    return typeof decoded.azp === "string" ? decoded.azp : null;
  } catch {
    return null;
  }
}

function parseAuthorizedParties(requestOrigin: string) {
  const configured = process.env.CLERK_AUTHORIZED_PARTIES
    ?.split(",")
    .map((value) => value.trim())
    .filter(Boolean);

  const parties = new Set<string>(configured ?? []);

  parties.add("http://localhost:3000");
  parties.add("https://underlytics.vercel.app");
  parties.add("https://underlytics-steve-mwangis-projects.vercel.app");
  parties.add("https://underlytics-git-main-steve-mwangis-projects.vercel.app");

  if (process.env.VERCEL_URL) {
    parties.add(`https://${process.env.VERCEL_URL}`);
  }

  if (requestOrigin) {
    parties.add(requestOrigin);
  }

  return [...parties];
}

function logClerkMiddlewareState(req: NextRequest, authorizedParties: string[]) {
  if (!CLERK_MIDDLEWARE_DEBUG) {
    return;
  }

  const sessionToken = req.cookies.get("__session")?.value;

  console.info(
    JSON.stringify({
      scope: "clerk-middleware",
      requestOrigin: req.nextUrl.origin,
      requestHost: req.nextUrl.host,
      requestPath: req.nextUrl.pathname,
      vercelUrl: process.env.VERCEL_URL ?? null,
      tokenAzp: decodeJwtAzp(sessionToken),
      candidateAuthorizedParties: authorizedParties,
      appliesAuthorizedParties: false,
    })
  );
}

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/applications(.*)",
  "/new-application(.*)",
]);

export default clerkMiddleware(
  async (auth, req) => {
    if (isProtectedRoute(req)) {
      await auth.protect();
    }
  },
  (req) => {
    const candidateAuthorizedParties = parseAuthorizedParties(req.nextUrl.origin);

    logClerkMiddlewareState(req, candidateAuthorizedParties);

    // Diagnostic mode: remove authorizedParties entirely to confirm whether
    // the unexpected-party error is coming from this middleware configuration.
    return {};
  }
);

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpg|jpeg|gif|png|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};

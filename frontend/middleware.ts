import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

function parseAuthorizedParties(requestOrigin: string) {
  const configured = process.env.CLERK_AUTHORIZED_PARTIES
    ?.split(",")
    .map((value) => value.trim())
    .filter(Boolean);

  const parties = new Set<string>(configured ?? []);

  parties.add("http://localhost:3000");
  parties.add("https://underlytics.vercel.app");

  if (process.env.VERCEL_URL) {
    parties.add(`https://${process.env.VERCEL_URL}`);
  }

  if (requestOrigin) {
    parties.add(requestOrigin);
  }

  return [...parties];
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
    return {
      authorizedParties: parseAuthorizedParties(req.nextUrl.origin),
    };
  }
);

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpg|jpeg|gif|png|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};

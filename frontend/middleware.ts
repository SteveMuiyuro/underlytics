import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

function parseAuthorizedParties() {
  const configured = process.env.CLERK_AUTHORIZED_PARTIES
    ?.split(",")
    .map((value) => value.trim())
    .filter(Boolean);

  if (configured?.length) {
    return configured;
  }

  return [
    "http://localhost:3000",
    "https://underlytics.vercel.app",
    // Vercel keeps additional production aliases active for the same deployment.
    // A session token can carry any of these origins in its azp claim.
    "https://underlytics-steve-mwangis-projects.vercel.app",
    "https://underlytics-git-main-steve-mwangis-projects.vercel.app",
  ];
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
  {
    authorizedParties: parseAuthorizedParties(),
  }
);

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpg|jpeg|gif|png|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};

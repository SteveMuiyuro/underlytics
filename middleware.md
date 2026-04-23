Fix the Clerk “unexpected party” error on the Vercel deployment.

Context:
- The live app is running at https://underlytics.vercel.app
- Error on /dashboard: “Clerk bearer token was issued for an unexpected party”
- This is caused by missing/incorrect authorizedParties in Clerk middleware

Task:
Update the Clerk middleware configuration to explicitly allow the production Vercel domain.

Implementation:

1. Update frontend/middleware.ts

Use this pattern:

import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

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
    authorizedParties: [
      "http://localhost:3000",
      "https://underlytics.vercel.app",
    ],
  }
);

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpg|jpeg|gif|png|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};

2. Ensure:
- authorizedParties includes both localhost (dev) and production domain
- no breaking changes to existing auth flow
- middleware still protects routes correctly

3. Do not modify:
- Clerk frontend setup
- backend auth logic
- routing structure

Goal:
- eliminate “unexpected party” error
- allow Clerk sessions issued for https://underlytics.vercel.app to be accepted
- restore access to /dashboard after login

After changes:
- commit and push
- allow Vercel to redeploy automatically
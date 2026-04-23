import { auth, currentUser } from "@clerk/nextjs/server";

import { getLoanProducts } from "@/lib/api/loan-products";
import { syncUser } from "@/lib/api/users";
import NewApplicationForm from "@/components/applications/new-application-form";
import { PageHeader } from "@/components/ui/page-header";

export default async function NewApplicationPage() {
  const { userId, getToken } = await auth();
  const clerkUser = await currentUser();

  if (!userId || !clerkUser) {
    return (
      <section className="space-y-6">
        <PageHeader
          eyebrow="Applications"
          title="New Loan Application"
          description="You must be signed in before starting a new underwriting request."
        />
        <p className="text-slate-600">
          You must be signed in to create an application.
        </p>
      </section>
    );
  }

  const primaryEmail =
    clerkUser.emailAddresses.find(
      (email) => email.id === clerkUser.primaryEmailAddressId
    )?.emailAddress ?? clerkUser.emailAddresses[0]?.emailAddress;

  if (!primaryEmail) {
    return (
      <section className="space-y-6">
        <PageHeader
          eyebrow="Applications"
          title="New Loan Application"
          description="An email address is required so the backend can sync the applicant profile."
        />
        <p className="text-slate-600">
          No email address is available for this account.
        </p>
      </section>
    );
  }

  const fullName =
    [clerkUser.firstName, clerkUser.lastName].filter(Boolean).join(" ") ||
    clerkUser.username ||
    "Applicant";

  const [loanProducts, backendUser] = await Promise.all([
    getLoanProducts(),
    getToken().then((token) => {
      if (!token) {
        throw new Error("Clerk session token is unavailable for backend sync");
      }

      return syncUser({
        clerk_user_id: userId,
        email: primaryEmail,
        full_name: fullName,
        phone_number: clerkUser.phoneNumbers[0]?.phoneNumber ?? null,
      }, { Authorization: `Bearer ${token}` });
    }),
  ]);

  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Applications"
        title="Start a New Loan Application"
        description="Capture applicant financials, choose a product, and prepare the case for planner-driven underwriting."
      />

      <NewApplicationForm
        loanProducts={loanProducts}
        applicantUserId={backendUser.id}
        applicantProfile={{
          fullName,
          email: primaryEmail,
          phoneNumber: clerkUser.phoneNumbers[0]?.phoneNumber ?? "",
        }}
      />
    </section>
  );
}

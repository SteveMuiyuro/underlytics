"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  BanknoteArrowDown,
  BriefcaseBusiness,
  Building2,
  FileCheck2,
  ShieldCheck,
} from "lucide-react";

import { createApplication } from "@/lib/api/create-application";
import { uploadDocument } from "@/lib/api/documents";
import { ApiLoanProduct } from "@/lib/types/api-loan-product";
import { formatCurrency } from "@/lib/underlytics-ui";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { StatusBadge } from "@/components/ui/status-badge";
import { Textarea } from "@/components/ui/textarea";

interface NewApplicationFormProps {
  loanProducts: ApiLoanProduct[];
  applicantUserId: string;
  applicantProfile: {
    fullName: string;
    email: string;
    phoneNumber: string;
  };
}

const COUNTRY_CODE_OPTIONS = [
  { label: "United States (+1)", code: "+1" },
  { label: "Canada (+1)", code: "+1" },
  { label: "United Kingdom (+44)", code: "+44" },
  { label: "Kenya (+254)", code: "+254" },
  { label: "Nigeria (+234)", code: "+234" },
  { label: "South Africa (+27)", code: "+27" },
  { label: "Uganda (+256)", code: "+256" },
  { label: "Tanzania (+255)", code: "+255" },
  { label: "India (+91)", code: "+91" },
  { label: "United Arab Emirates (+971)", code: "+971" },
  { label: "Germany (+49)", code: "+49" },
  { label: "France (+33)", code: "+33" },
];

function getPhoneDefaults(phoneNumber: string) {
  const normalized = phoneNumber.replace(/[^\d+]/g, "");
  const matchedOption = [...COUNTRY_CODE_OPTIONS]
    .sort((left, right) => right.code.length - left.code.length)
    .find((option) => normalized.startsWith(option.code));

  if (!matchedOption) {
    return {
      countryCode: "+1",
      localNumber: normalized.replace(/^\+/, ""),
    };
  }

  return {
    countryCode: matchedOption.code,
    localNumber: normalized.slice(matchedOption.code.length).replace(/[^\d]/g, ""),
  };
}

export default function NewApplicationForm({
  loanProducts,
  applicantUserId,
  applicantProfile,
}: NewApplicationFormProps) {
  const router = useRouter();
  const phoneDefaults = getPhoneDefaults(applicantProfile.phoneNumber);

  const [formData, setFormData] = useState({
    applicant_user_id: applicantUserId,
    loan_product_id: "",
    requested_amount: "",
    requested_term_months: "",
    loan_purpose: "",
    monthly_income: "",
    monthly_expenses: "",
    existing_loan_obligations: "",
    employment_status: "",
    employer_name: "",
    bank_name: "",
    account_type: "",
    phone_country_code: phoneDefaults.countryCode,
    phone_number: phoneDefaults.localNumber,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [documentFiles, setDocumentFiles] = useState<{
    id_document: File | null;
    payslip: File | null;
    bank_statement: File | null;
  }>({
    id_document: null,
    payslip: null,
    bank_statement: null,
  });

  const fileInputRefs = useRef<{
    id_document: HTMLInputElement | null;
    payslip: HTMLInputElement | null;
    bank_statement: HTMLInputElement | null;
  }>({
    id_document: null,
    payslip: null,
    bank_statement: null,
  });

  const selectedProduct =
    loanProducts.find((product) => product.id === formData.loan_product_id) ?? null;
  const requestedAmount = Number(formData.requested_amount || 0);
  const monthlyIncome = Number(formData.monthly_income || 0);
  const monthlyExpenses = Number(formData.monthly_expenses || 0);
  const obligations = Number(formData.existing_loan_obligations || 0);
  const monthlyBuffer = Math.max(monthlyIncome - monthlyExpenses - obligations, 0);
  const selectedDocumentCount = Object.values(documentFiles).filter(Boolean).length;
  const missingDocumentLabels = [
    !documentFiles.id_document ? "ID Document" : null,
    !documentFiles.payslip ? "Payslip" : null,
    !documentFiles.bank_statement ? "Bank Statement" : null,
  ].filter(Boolean) as string[];
  const allRequiredDocumentsSelected = missingDocumentLabels.length === 0;

  function updateField(name: string, value: string) {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  }

  function updateDocumentFile(
    documentType: "id_document" | "payslip" | "bank_statement",
    file: File | null
  ) {
    setDocumentFiles((prev) => ({
      ...prev,
      [documentType]: file,
    }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const application = await createApplication({
        applicant_user_id: formData.applicant_user_id,
        loan_product_id: formData.loan_product_id,
        requested_amount: Number(formData.requested_amount),
        requested_term_months: Number(formData.requested_term_months),
        loan_purpose: formData.loan_purpose,
        monthly_income: Number(formData.monthly_income),
        monthly_expenses: Number(formData.monthly_expenses),
        existing_loan_obligations: Number(formData.existing_loan_obligations || 0),
        employment_status: formData.employment_status,
        employer_name: formData.employer_name,
        bank_name: formData.bank_name,
        account_type: formData.account_type,
        auto_start_workflow: false,
      });

      const uploads: Array<{
        documentType: "id_document" | "payslip" | "bank_statement";
        file: File;
        triggerWorkflow: boolean;
      }> = [
        {
          documentType: "id_document",
          file: documentFiles.id_document as File,
          triggerWorkflow: false,
        },
        {
          documentType: "payslip",
          file: documentFiles.payslip as File,
          triggerWorkflow: false,
        },
        {
          documentType: "bank_statement",
          file: documentFiles.bank_statement as File,
          triggerWorkflow: true,
        },
      ];

      for (const upload of uploads) {
        await uploadDocument({
          applicationId: application.id,
          documentType: upload.documentType,
          file: upload.file,
          triggerWorkflow: upload.triggerWorkflow,
        });
      }

      setDocumentFiles({
        id_document: null,
        payslip: null,
        bank_statement: null,
      });
      for (const input of Object.values(fileInputRefs.current)) {
        if (input) {
          input.value = "";
        }
      }

      router.push(`/applications/${application.application_number}/processing`);
      router.refresh();
    } catch {
      setError(
        "Something went wrong while submitting the application or uploading documents."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Card className="page-surface py-0">
            <CardHeader className="border-b border-slate-200/70 py-6">
              <CardTitle>Applicant Information</CardTitle>
              <CardDescription>
                Identity and profile details linked to the signed-in account.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-5 py-6 md:grid-cols-2">
              <FormField>
                <FormItem>
                  <FormLabel>Full Name</FormLabel>
                  <FormControl>
                    <Input value={applicantProfile.fullName} readOnly />
                  </FormControl>
                  <FormDescription>Synced from your authenticated profile.</FormDescription>
                </FormItem>
              </FormField>

              <FormField>
                <FormItem>
                  <FormLabel>Email Address</FormLabel>
                  <FormControl>
                    <Input value={applicantProfile.email} type="email" readOnly />
                  </FormControl>
                  <FormDescription>Used for application notifications later.</FormDescription>
                </FormItem>
              </FormField>

              <FormField className="md:col-span-2">
                <FormItem>
                  <FormLabel>Phone Number</FormLabel>
                  <FormControl>
                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                      <Select
                        value={formData.phone_country_code}
                        onValueChange={(value) =>
                          updateField("phone_country_code", value)
                        }
                        options={COUNTRY_CODE_OPTIONS.map((option) => ({
                          label: option.label,
                          value: option.code,
                        }))}
                        className="min-w-0"
                      />
                      <Input
                        placeholder="Enter local phone number"
                        value={formData.phone_number}
                        onChange={(e) =>
                          updateField(
                            "phone_number",
                            e.target.value.replace(/\D/g, "")
                          )
                        }
                        inputMode="numeric"
                        pattern="[0-9]*"
                      />
                    </div>
                  </FormControl>
                  <FormDescription>
                    Select the country calling code, then enter the local number.
                  </FormDescription>
                </FormItem>
              </FormField>

              <FormField className="md:col-span-2">
                <FormItem>
                  <FormLabel>Employment Status</FormLabel>
                  <FormControl>
                    <Select
                      value={formData.employment_status}
                      onValueChange={(value) =>
                        updateField("employment_status", value)
                      }
                      placeholder="Select employment status"
                      options={[
                        { label: "Full Time", value: "full_time" },
                        { label: "Part Time", value: "part_time" },
                        { label: "Self Employed", value: "self_employed" },
                        { label: "Contract", value: "contract" },
                        { label: "Unemployed", value: "unemployed" },
                      ]}
                    />
                  </FormControl>
                </FormItem>
              </FormField>

              <FormField className="md:col-span-2">
                <FormItem>
                  <FormLabel>Employer Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Employer or business name"
                      value={formData.employer_name}
                      onChange={(e) => updateField("employer_name", e.target.value)}
                    />
                  </FormControl>
                </FormItem>
              </FormField>
            </CardContent>
          </Card>

          <Card className="page-surface py-0">
            <CardHeader className="border-b border-slate-200/70 py-6">
              <CardTitle>Loan Request</CardTitle>
              <CardDescription>
                Choose the product, define the request, and state the funding purpose.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-5 py-6 md:grid-cols-2">
              <FormField className="md:col-span-2">
                <FormItem>
                  <FormLabel>Loan Product</FormLabel>
                  <FormControl>
                    <Select
                      value={formData.loan_product_id}
                      onValueChange={(value) => updateField("loan_product_id", value)}
                      placeholder="Select loan product"
                      options={loanProducts.map((product) => ({
                        label: product.name,
                        value: product.id,
                      }))}
                      required
                    />
                  </FormControl>
                  {selectedProduct ? (
                    <FormDescription>
                      {selectedProduct.description ||
                        `${formatCurrency(selectedProduct.min_amount)} to ${formatCurrency(selectedProduct.max_amount)} across ${selectedProduct.min_term_months} to ${selectedProduct.max_term_months} months.`}
                    </FormDescription>
                  ) : null}
                </FormItem>
              </FormField>

              <FormField>
                <FormItem>
                  <FormLabel>Requested Amount</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="250000"
                      type="number"
                      value={formData.requested_amount}
                      onChange={(e) => updateField("requested_amount", e.target.value)}
                      required
                    />
                  </FormControl>
                </FormItem>
              </FormField>

              <FormField>
                <FormItem>
                  <FormLabel>Preferred Term (Months)</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="12"
                      type="number"
                      value={formData.requested_term_months}
                      onChange={(e) => updateField("requested_term_months", e.target.value)}
                      required
                    />
                  </FormControl>
                </FormItem>
              </FormField>

              <FormField className="md:col-span-2">
                <FormItem>
                  <FormLabel>Loan Purpose</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe how the funds will be used."
                      value={formData.loan_purpose}
                      onChange={(e) => updateField("loan_purpose", e.target.value)}
                    />
                  </FormControl>
                </FormItem>
              </FormField>
            </CardContent>
          </Card>

          <Card className="page-surface py-0">
            <CardHeader className="border-b border-slate-200/70 py-6">
              <CardTitle>Financial Information</CardTitle>
              <CardDescription>
                These values feed the risk worker’s income, expense, and obligation checks.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-5 py-6 md:grid-cols-2">
              <FormField>
                <FormItem>
                  <FormLabel>Monthly Income</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="120000"
                      type="number"
                      value={formData.monthly_income}
                      onChange={(e) => updateField("monthly_income", e.target.value)}
                      required
                    />
                  </FormControl>
                </FormItem>
              </FormField>

              <FormField>
                <FormItem>
                  <FormLabel>Monthly Expenses</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="45000"
                      type="number"
                      value={formData.monthly_expenses}
                      onChange={(e) => updateField("monthly_expenses", e.target.value)}
                      required
                    />
                  </FormControl>
                </FormItem>
              </FormField>

              <FormField>
                <FormItem>
                  <FormLabel>Existing Loan Obligations</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="0"
                      type="number"
                      value={formData.existing_loan_obligations}
                      onChange={(e) =>
                        updateField("existing_loan_obligations", e.target.value)
                      }
                    />
                  </FormControl>
                </FormItem>
              </FormField>

              <FormField>
                <FormItem>
                  <FormLabel>Bank Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Primary banking institution"
                      value={formData.bank_name}
                      onChange={(e) => updateField("bank_name", e.target.value)}
                    />
                  </FormControl>
                </FormItem>
              </FormField>

              <FormField className="md:col-span-2">
                <FormItem>
                  <FormLabel>Account Type</FormLabel>
                  <FormControl>
                    <Select
                      value={formData.account_type}
                      onValueChange={(value) => updateField("account_type", value)}
                      placeholder="Select account type"
                      options={[
                        { label: "Current", value: "current" },
                        { label: "Savings", value: "savings" },
                        { label: "Salary", value: "salary" },
                        { label: "Business", value: "business" },
                      ]}
                    />
                  </FormControl>
                </FormItem>
              </FormField>
            </CardContent>
          </Card>

          <Card className="page-surface py-0">
            <CardHeader className="border-b border-slate-200/70 py-6">
              <CardTitle>Supporting Documents</CardTitle>
              <CardDescription>
                Choose any supporting documents now. Selected files are uploaded
                automatically right after the application record is created.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 py-6">
              <div className="rounded-[24px] border border-dashed border-slate-300 bg-slate-50/80 p-5">
                <div className="flex items-start gap-4">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-indigo-600 shadow-sm">
                    <FileCheck2 className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-slate-900">ID Document</p>
                    <p className="mt-1 text-sm leading-6 text-slate-500">
                      Add a government-issued identification document for document validation.
                    </p>
                    <div className="mt-4 space-y-3">
                      <input
                        ref={(node) => {
                          fileInputRefs.current.id_document = node;
                        }}
                        type="file"
                        onChange={(e) =>
                          updateDocumentFile("id_document", e.target.files?.[0] ?? null)
                        }
                        className="block w-full rounded-2xl border border-white bg-white px-4 py-3 text-sm text-slate-600 shadow-xs"
                      />
                      {documentFiles.id_document ? (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <ShieldCheck className="size-4 text-emerald-600" />
                          <p className="truncate">Selected: {documentFiles.id_document.name}</p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-[24px] border border-dashed border-slate-300 bg-slate-50/80 p-5">
                <div className="flex items-start gap-4">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-cyan-700 shadow-sm">
                    <BriefcaseBusiness className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-slate-900">Payslip</p>
                    <p className="mt-1 text-sm leading-6 text-slate-500">
                      Provide the latest earnings evidence to support income validation.
                    </p>
                    <div className="mt-4 space-y-3">
                      <input
                        ref={(node) => {
                          fileInputRefs.current.payslip = node;
                        }}
                        type="file"
                        onChange={(e) =>
                          updateDocumentFile("payslip", e.target.files?.[0] ?? null)
                        }
                        className="block w-full rounded-2xl border border-white bg-white px-4 py-3 text-sm text-slate-600 shadow-xs"
                      />
                      {documentFiles.payslip ? (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <ShieldCheck className="size-4 text-emerald-600" />
                          <p className="truncate">Selected: {documentFiles.payslip.name}</p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-[24px] border border-dashed border-slate-300 bg-slate-50/80 p-5">
                <div className="flex items-start gap-4">
                  <div className="flex size-11 items-center justify-center rounded-2xl bg-white text-emerald-700 shadow-sm">
                    <Building2 className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-slate-900">Bank Statement</p>
                    <p className="mt-1 text-sm leading-6 text-slate-500">
                      Add a recent bank statement so underwriting can verify repayment capacity.
                    </p>
                    <div className="mt-4 space-y-3">
                      <input
                        ref={(node) => {
                          fileInputRefs.current.bank_statement = node;
                        }}
                        type="file"
                        onChange={(e) =>
                          updateDocumentFile(
                            "bank_statement",
                            e.target.files?.[0] ?? null
                          )
                        }
                        className="block w-full rounded-2xl border border-white bg-white px-4 py-3 text-sm text-slate-600 shadow-xs"
                      />
                      {documentFiles.bank_statement ? (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <ShieldCheck className="size-4 text-emerald-600" />
                          <p className="truncate">
                            Selected: {documentFiles.bank_statement.name}
                          </p>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="page-surface py-0">
            <CardHeader className="border-b border-slate-200/70 py-6">
              <CardTitle>Application Summary</CardTitle>
              <CardDescription>
                A live overview of the request that will be sent into underwriting.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5 py-6 text-sm">
              <div className="rounded-[24px] bg-slate-950 p-5 text-white">
                <p className="text-sm text-white/65">Requested amount</p>
                <p className="mt-3 text-3xl font-semibold tracking-tight">
                  {requestedAmount ? formatCurrency(requestedAmount) : "Not entered"}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <StatusBadge tone="cyan">
                    {formData.requested_term_months
                      ? `${formData.requested_term_months} months`
                      : "term pending"}
                  </StatusBadge>
                  <StatusBadge tone="indigo">
                    {selectedProduct?.name ?? "product pending"}
                  </StatusBadge>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                <div className="rounded-[22px] border border-slate-200/80 bg-slate-50/80 p-4">
                  <div className="flex items-center gap-2 text-slate-500">
                    <BanknoteArrowDown className="size-4" />
                    <p>Monthly buffer</p>
                  </div>
                  <p className="mt-2 text-lg font-semibold text-slate-900">
                    {monthlyIncome || monthlyExpenses || obligations
                      ? formatCurrency(monthlyBuffer)
                      : "Awaiting inputs"}
                  </p>
                </div>

                <div className="rounded-[22px] border border-slate-200/80 bg-slate-50/80 p-4">
                  <p className="text-slate-500">Document center</p>
                  <p className="mt-2 text-lg font-semibold text-slate-900">
                    {allRequiredDocumentsSelected
                      ? "All required files ready"
                      : `${selectedDocumentCount}/3 files selected`}
                  </p>
                </div>
              </div>

              <div className="space-y-4 rounded-[24px] border border-slate-200/80 bg-white p-5">
                <div>
                  <p className="text-slate-500">Loan Product</p>
                  <p className="mt-1 font-medium text-slate-900">
                    {selectedProduct?.name ?? "Not selected"}
                  </p>
                </div>

                <div>
                  <p className="text-slate-500">Income vs expenses</p>
                  <p className="mt-1 font-medium text-slate-900">
                    {monthlyIncome
                      ? `${formatCurrency(monthlyIncome)} income / ${formatCurrency(monthlyExpenses || 0)} expenses`
                      : "Not entered"}
                  </p>
                </div>

                <div>
                  <p className="text-slate-500">Submission status</p>
                  <div className="mt-2">
                    <StatusBadge tone="amber">ready for underwriting</StatusBadge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {error ? (
            <FormMessage className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3">
              {error}
            </FormMessage>
          ) : null}

          {!allRequiredDocumentsSelected ? (
            <FormMessage className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800">
              Upload all required documents before submission:{" "}
              {missingDocumentLabels.join(", ")}.
            </FormMessage>
          ) : null}

          <div className="flex flex-col gap-3">
            <Button
              type="submit"
              className="h-11 w-full rounded-2xl"
              disabled={isSubmitting || !allRequiredDocumentsSelected}
            >
              {isSubmitting
                ? "Submitting and Starting Evaluation..."
                : "Submit Application"}
            </Button>

            <Button type="button" variant="outline" className="h-11 w-full rounded-2xl" disabled>
              Save as Draft Soon
            </Button>
          </div>
        </div>
      </div>
    </Form>
  );
}

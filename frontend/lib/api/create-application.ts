export interface CreateApplicationPayload {
  applicant_user_id: string;
  loan_product_id: string;
  requested_amount: number;
  requested_term_months: number;
  loan_purpose?: string;
  monthly_income: number;
  monthly_expenses: number;
  existing_loan_obligations?: number;
  employment_status?: string;
  employer_name?: string;
  bank_name?: string;
  account_type?: string;
}

export async function createApplication(payload: CreateApplicationPayload) {
  const response = await fetch(`/api/applications`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to create application");
  }

  return response.json();
}

export interface ApiApplication {
  id: string;
  application_number: string;
  applicant_user_id: string;
  loan_product_id: string;
  status: string;
  requested_amount: number;
  requested_term_months: number;
  loan_purpose: string | null;
  monthly_income: number;
  monthly_expenses: number;
  existing_loan_obligations: number;
  employment_status: string | null;
  employer_name: string | null;
  bank_name: string | null;
  account_type: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
}
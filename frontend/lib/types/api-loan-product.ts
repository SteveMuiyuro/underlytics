export interface ApiLoanProduct {
  id: string;
  code: string;
  name: string;
  description: string | null;
  min_amount: number;
  max_amount: number;
  min_term_months: number;
  max_term_months: number;
  is_active: boolean;
}
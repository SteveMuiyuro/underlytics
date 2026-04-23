export interface ApiManualReviewAction {
  id: string;
  manual_review_case_id: string;
  reviewer_user_id: string;
  action: string;
  note: string;
  old_decision: string | null;
  new_decision: string | null;
  created_at: string;
}

export interface ApiManualReviewCaseSummary {
  id: string;
  application_id: string;
  application_number: string;
  application_status: string;
  requested_amount: number;
  applicant_user_id: string;
  workflow_plan_id: string;
  workflow_plan_status: string;
  status: string;
  reason: string;
  assigned_reviewer_user_id: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface ApiManualReviewCaseDetail extends ApiManualReviewCaseSummary {
  actions: ApiManualReviewAction[];
}

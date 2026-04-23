export interface ApiUnderwritingJob {
  id: string;
  application_id: string;
  status: string;
  current_step: string | null;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export interface ApiAgentRun {
  id: string;
  underwriting_job_id: string;
  application_id: string;
  agent_name: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  retry_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}
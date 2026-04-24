export interface ApiWorkflowStatusAgent {
  name: string;
  label: string;
  status: "pending" | "running" | "completed" | "failed";
  snippet: string;
  reasoning: string | null;
  decision: string | null;
}

export interface ApiWorkflowStatus {
  application_number: string;
  status: "processing" | "completed" | "failed";
  progress: number;
  current_stage: string;
  agents: ApiWorkflowStatusAgent[];
}

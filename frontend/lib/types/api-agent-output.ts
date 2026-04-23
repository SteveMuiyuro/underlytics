export interface ApiAgentOutput {
  id: string;
  agent_run_id: string;
  application_id: string;
  agent_name: string;
  score: number | null;
  confidence: number | null;
  decision: string | null;
  flags: string | null;
  reasoning: string | null;
  output_json: string;
  created_at: string;
  updated_at: string;
}
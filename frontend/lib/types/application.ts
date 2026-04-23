export type ApplicationStatus =
  | "Draft"
  | "In Progress"
  | "Approved"
  | "Rejected"
  | "Manual Review";

export interface Application {
  id: string;
  name: string;
  amount: string;
  product: string;
  status: ApplicationStatus;
}

export interface AgentFinding {
  title: string;
  status: string;
  summary: string;
}
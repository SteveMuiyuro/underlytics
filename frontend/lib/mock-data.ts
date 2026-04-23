import { AgentFinding, Application } from "@/lib/types/application";

export const applications: Application[] = [
  {
    id: "APP-001",
    name: "John Doe",
    amount: "$5,000",
    product: "Personal Loan",
    status: "In Progress",
  },
  {
    id: "APP-002",
    name: "Jane Smith",
    amount: "$3,000",
    product: "Salary Advance",
    status: "Approved",
  },
  {
    id: "APP-003",
    name: "Michael Brown",
    amount: "$10,000",
    product: "Business Loan",
    status: "Rejected",
  },
];

export const agentFindings: AgentFinding[] = [
  {
    title: "Document Analysis Agent",
    status: "Completed",
    summary:
      "Payslip and bank statement were successfully parsed. Monthly income identified as $2,400.",
  },
  {
    title: "Policy Retrieval Agent",
    status: "Completed",
    summary:
      "Matched personal loan policy and confirmed applicant meets minimum income threshold.",
  },
  {
    title: "Risk Assessment Agent",
    status: "Completed",
    summary:
      "Debt-to-income ratio calculated at 28 percent. Risk band assessed as low.",
  },
  {
    title: "Fraud Verification Agent",
    status: "Completed",
    summary:
      "No identity mismatches or suspicious inconsistencies were detected.",
  },
];

export const timeline = [
  "Application submitted",
  "Documents uploaded",
  "Document analysis completed",
  "Policy retrieval completed",
  "Risk scoring completed",
  "Fraud verification completed",
  "Decision generated",
  "Decision email sent",
];
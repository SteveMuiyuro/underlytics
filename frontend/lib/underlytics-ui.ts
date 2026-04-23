export type StatusTone =
  | "neutral"
  | "indigo"
  | "cyan"
  | "green"
  | "amber"
  | "red"
  | "slate";

export function formatCurrency(amount: number) {
  return `$${amount.toLocaleString()}`;
}

export function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "N/A";
  }

  return `${Math.round(value * 100)}%`;
}

export function humanize(value: string | null | undefined) {
  if (!value) {
    return "N/A";
  }

  return value.replaceAll("_", " ");
}

export function parseFlags(flags: string | null): string[] {
  if (!flags) {
    return [];
  }

  try {
    const parsed = JSON.parse(flags);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function formatDocumentType(type: string) {
  const labels: Record<string, string> = {
    id_document: "ID Document",
    payslip: "Payslip",
    bank_statement: "Bank Statement",
  };

  return labels[type] ?? humanize(type);
}

export function formatAgentName(name: string) {
  const labels: Record<string, string> = {
    document_analysis: "Document Analysis Worker",
    policy_retrieval: "Policy Retrieval Worker",
    risk_assessment: "Risk Assessment Worker",
    fraud_verification: "Fraud Verification Worker",
    decision_summary: "Decision Summary Worker",
  };

  return labels[name] ?? humanize(name);
}

export function formatWorkflowStep(step: string | null) {
  return humanize(step);
}

export function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function getApplicationStatusMeta(status: string) {
  const meta: Record<string, { label: string; tone: StatusTone }> = {
    approved: { label: "Approved", tone: "green" },
    rejected: { label: "Rejected", tone: "red" },
    manual_review: { label: "Manual Review", tone: "amber" },
    draft: { label: "Draft", tone: "neutral" },
    submitted: { label: "Submitted", tone: "cyan" },
    in_progress: { label: "In Progress", tone: "indigo" },
  };

  return meta[status] ?? { label: humanize(status), tone: "neutral" as StatusTone };
}

export function getWorkflowStatusMeta(status: string) {
  const meta: Record<string, { label: string; tone: StatusTone }> = {
    completed: { label: "Completed", tone: "green" },
    failed: { label: "Failed", tone: "red" },
    running: { label: "Running", tone: "cyan" },
    retried: { label: "Retried", tone: "amber" },
    pending: { label: "Pending", tone: "neutral" },
  };

  return meta[status] ?? { label: humanize(status), tone: "neutral" as StatusTone };
}

export function getManualReviewStatusMeta(status: string) {
  if (status === "resolved") {
    return { label: "Resolved", tone: "green" as StatusTone };
  }

  return { label: "Open", tone: "amber" as StatusTone };
}

export function getRoleMeta(role: string) {
  const meta: Record<string, { label: string; tone: StatusTone }> = {
    admin: { label: "Admin", tone: "slate" },
    reviewer: { label: "Reviewer", tone: "cyan" },
    applicant: { label: "Applicant", tone: "neutral" },
  };

  return meta[role] ?? { label: humanize(role), tone: "neutral" as StatusTone };
}

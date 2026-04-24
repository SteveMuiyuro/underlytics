export async function uploadDocument(payload: {
  applicationId: string;
  documentType: string;
  file: File;
  triggerWorkflow?: boolean;
}) {
  const formData = new FormData();
  formData.append("application_id", payload.applicationId);
  formData.append("document_type", payload.documentType);
  formData.append("file", payload.file);
  formData.append("trigger_workflow", String(payload.triggerWorkflow ?? true));

  const response = await fetch(`/api/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload document");
  }

  return response.json();
}

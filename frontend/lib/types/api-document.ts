export interface ApiDocument {
  id: string;
  application_id: string;
  document_type: string;
  file_name: string;
  file_path: string;
  mime_type: string;
  file_size_bytes: number;
  upload_status: string;
  is_required: boolean;
  uploaded_at: string;
  created_at: string;
  updated_at: string;
}
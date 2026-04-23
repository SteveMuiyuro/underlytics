from datetime import datetime

from pydantic import BaseModel


class ApplicationDocumentResponse(BaseModel):
    id: str
    application_id: str
    document_type: str
    file_name: str
    file_path: str
    mime_type: str
    file_size_bytes: int
    upload_status: str
    is_required: bool
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
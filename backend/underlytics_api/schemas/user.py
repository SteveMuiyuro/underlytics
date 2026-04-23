from pydantic import BaseModel


class UserSyncRequest(BaseModel):
    clerk_user_id: str
    email: str
    full_name: str
    phone_number: str | None = None
    role: str | None = None


class UserResponse(BaseModel):
    id: str
    clerk_user_id: str
    role: str
    email: str
    full_name: str
    phone_number: str | None

    model_config = {"from_attributes": True}

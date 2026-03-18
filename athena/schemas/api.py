from datetime import datetime

from pydantic import BaseModel


class PromptRequest(BaseModel):
    prompt: str
    images: list[str] | None = None


class SessionResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SessionItemResponse(BaseModel):
    id: int
    session_id: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True

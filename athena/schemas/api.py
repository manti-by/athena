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


class SessionItemImageResponse(BaseModel):
    id: int
    file_path: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionItemDetailResponse(BaseModel):
    id: int
    session_id: int
    text: str
    created_at: datetime
    images: list[SessionItemImageResponse]

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    items: list[SessionItemDetailResponse]

    class Config:
        from_attributes = True

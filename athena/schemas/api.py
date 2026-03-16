from pydantic import BaseModel


class PromptRequest(BaseModel):
    prompt: str
    images: list[str] | None = None

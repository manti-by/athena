from pydantic import BaseModel


class TokenData(BaseModel):
    user_id: int
    email: str


class GoogleUserInfo(BaseModel):
    id: str
    email: str
    name: str | None
    picture: str | None

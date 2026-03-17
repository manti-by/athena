from datetime import UTC, datetime, timedelta
from typing import Any

import google.auth.transport.requests
import requests
from fastapi import Request
from google.oauth2.id_token import verify_oauth2_token
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from athena.models.user import User
from athena.schemas.google import GoogleUserInfo, TokenData
from athena.settings import get_settings


settings = get_settings()


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        if user_id is None or email is None:
            return None
        return TokenData(user_id=user_id, email=email)
    except JWTError:
        return None


def get_google_auth_url() -> str:
    client_id = settings.GOOGLE_CLIENT_ID
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    scope = "openid email profile"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline"
    )
    return auth_url


def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    token_url = "https://oauth2.googleapis.com/token"  # nosec: B105
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def get_google_user_info(id_token: str) -> GoogleUserInfo:
    request = google.auth.transport.requests.Request()
    info = verify_oauth2_token(id_token, request, settings.GOOGLE_CLIENT_ID)
    return GoogleUserInfo(
        id=info["sub"],
        email=info["email"],
        name=info.get("name"),
        picture=info.get("picture"),
    )


async def get_or_create_user(session: AsyncSession, google_info: GoogleUserInfo) -> User:
    stmt = select(User).where(User.google_id == google_info.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        stmt = select(User).where(User.email == google_info.email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                google_id=google_info.id,
                email=google_info.email,
                name=google_info.name,
                avatar=google_info.picture,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            user.google_id = google_info.id
            user.avatar = google_info.picture
            await session.commit()

    return user


async def get_current_user(session: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None
    token_data = verify_token(token)
    if not token_data:
        return None
    stmt = select(User).where(User.id == token_data.user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_from_request(request: Request, session: AsyncSession) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    return await get_current_user(session, token)

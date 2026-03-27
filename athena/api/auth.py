from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from athena.services.auth import (
    TokenData,
    create_access_token,
    exchange_code_for_tokens,
    get_current_user,
    get_google_auth_url,
    get_google_user_info,
    get_or_create_user,
)


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/google/login")
async def google_login():
    auth_url = get_google_auth_url()
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(code: str, request: Request):
    tokens = exchange_code_for_tokens(code=code)
    id_token = tokens["id_token"]

    google_info = get_google_user_info(id_token)
    user = await get_or_create_user(google_info=google_info)

    token_data = TokenData(user_id=user.id, email=user.email)
    access_token = create_access_token(data=token_data.model_dump())

    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/me")
async def get_me(request: Request):
    if not (token := request.cookies.get("access_token")):
        return {"authenticated": False}

    if not (user := await get_current_user(token=token)):
        return {"authenticated": False}

    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar,
        },
    }


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

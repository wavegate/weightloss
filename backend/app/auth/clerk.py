from functools import lru_cache

from clerk_backend_api.security import (
    AuthenticateRequestOptions,
    authenticate_request,
)
from fastapi import Depends, HTTPException, Request

from app.config import _env


@lru_cache
def _auth_options() -> AuthenticateRequestOptions:
    return AuthenticateRequestOptions(secret_key=_env("CLERK_SECRET_KEY"))


def get_current_user_id(request: Request) -> str:
    state = authenticate_request(request, _auth_options())

    if not state.is_signed_in or not state.payload:
        raise HTTPException(
            status_code=401,
            detail=state.message or "Unauthorized",
        )

    user_id = state.payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session token")

    return user_id


CurrentUserId = Depends(get_current_user_id)

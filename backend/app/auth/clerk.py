from collections.abc import Mapping
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


def _user_id_from_auth_state(state) -> str:
    if not state.is_signed_in or not state.payload:
        raise HTTPException(
            status_code=401,
            detail=state.message or "Unauthorized",
        )

    user_id = state.payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session token")

    return user_id


def get_current_user_id(request: Request) -> str:
    return _user_id_from_auth_state(authenticate_request(request, _auth_options()))


def get_user_id_from_headers(headers: Mapping[str, str]) -> str:
    authorization = headers.get("authorization") or headers.get("Authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    scope = {
        "type": "http",
        "headers": [(b"authorization", authorization.encode("latin-1"))],
        "method": "POST",
        "path": "/copilotkit",
    }
    request = Request(scope)
    return _user_id_from_auth_state(authenticate_request(request, _auth_options()))


CurrentUserId = Depends(get_current_user_id)

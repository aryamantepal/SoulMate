"""FastAPI auth dependency: verify a Supabase access token via Supabase Auth.

We never decode the JWT ourselves. The frontend signs in with `supabase-js` and
sends `Authorization: Bearer <access_token>`; we hand that token to Supabase's
`/auth/v1/user` endpoint (via supabase-py) and let Supabase tell us who the user
is. No `SUPABASE_JWT_SECRET`, no JWKS plumbing on our side.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import AsyncClient, create_async_client

logger = logging.getLogger("solemate.auth")
bearer = HTTPBearer(auto_error=False)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{name} is not configured",
        )
    return value


@lru_cache(maxsize=1)
def _client_factory_key() -> tuple[str, str]:
    return _required_env("SUPABASE_URL"), _required_env("SUPABASE_ANON_KEY")


_client: AsyncClient | None = None


async def _get_client() -> AsyncClient:
    global _client
    if _client is None:
        url, anon_key = _client_factory_key()
        _client = await create_async_client(url, anon_key)
    return _client


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    client = await _get_client()
    token = credentials.credentials
    try:
        response = await client.auth.get_user(token)
    except Exception as exc:
        logger.warning(
            "supabase auth.get_user raised: %s (token prefix=%s)",
            exc,
            token[:12],
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid bearer token: {exc}",
        ) from exc

    user = getattr(response, "user", None)
    if user is None or not getattr(user, "id", None):
        logger.warning(
            "supabase auth.get_user returned no user (response=%r)", response
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token (no user in response)",
        )

    return user.id

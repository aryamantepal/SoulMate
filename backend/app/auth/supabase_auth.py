"""FastAPI auth dependency: verify a Supabase access token via JWKS.

Modern Supabase projects sign access tokens with an **asymmetric** key (ES256/
EdDSA) and publish the matching public keys at
`<SUPABASE_URL>/auth/v1/.well-known/jwks.json`. We fetch + cache those public
keys and verify the JWT's signature locally — Supabase signs, we check.

That means:
- No `SUPABASE_JWT_SECRET` (and no shared secret of any kind on our side).
- No network round-trip per request once the JWKS is cached.
- Verification is cryptographic, not "Supabase Auth happens to be reachable."

The frontend signs in with `supabase-js` and sends
`Authorization: Bearer <access_token>`; we trust the `sub` claim Supabase
signed only after the signature checks out.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

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
def _jwks_client() -> PyJWKClient:
    url = _required_env("SUPABASE_URL").rstrip("/")
    return PyJWKClient(f"{url}/auth/v1/.well-known/jwks.json", cache_keys=True)


_VERIFY_ALGS = ("ES256", "EdDSA", "RS256")


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = credentials.credentials
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=list(_VERIFY_ALGS),
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        logger.warning("jwt verify failed: %s (token prefix=%s)", exc, token[:12])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid bearer token: {exc}",
        ) from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing a subject",
        )

    return user_id

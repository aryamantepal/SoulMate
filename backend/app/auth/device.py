"""Anonymous identity: each browser sends a random device ID in `X-Device-Id`."""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import Header, HTTPException, status

_DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")


async def current_user(
    x_device_id: Annotated[str | None, Header()] = None,
) -> str:
    if not x_device_id or not _DEVICE_ID_RE.fullmatch(x_device_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Device-Id header",
        )
    return x_device_id

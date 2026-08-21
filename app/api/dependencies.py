from typing import Annotated

from fastapi import Header, HTTPException

from app.core.config import settings


async def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

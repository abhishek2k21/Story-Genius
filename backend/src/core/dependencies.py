"""
FastAPI Dependencies
Provides dependency injection for database sessions, settings, and authentication.
"""
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import Settings, get_settings
from src.database.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.

    Usage:
        @router.get("/items")
        async def get_items(db: DbSession):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_current_settings() -> Settings:
    """Settings dependency."""
    return get_settings()


async def get_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Extract API key from headers.
    Accepts either X-API-Key header or Bearer token.
    """
    if x_api_key:
        return x_api_key

    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> str | None:
    """Optional API key - returns None if not provided."""
    if x_api_key:
        return x_api_key
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


# Type aliases for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentSettings = Annotated[Settings, Depends(get_current_settings)]
ApiKey = Annotated[str, Depends(get_api_key)]
OptionalApiKey = Annotated[str | None, Depends(get_optional_api_key)]

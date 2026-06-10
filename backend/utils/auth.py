from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.database import User, get_session

_ALGORITHM = "HS256"
_TOKEN_LIFETIME = timedelta(days=14)
_PBKDF2_ROUNDS = 200_000

_bearer = HTTPBearer(auto_error=False)


def hash_password(raw_password: str, *, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ROUNDS)
    return digest.hex(), salt


def verify_password(raw_password: str, *, password_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(raw_password, salt=salt)
    return hmac.compare_digest(candidate, password_hash)


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + _TOKEN_LIFETIME
    return jwt.encode({"sub": user_id, "exp": expires_at}, settings.secret_key, algorithm=_ALGORITHM)


def _decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That session has expired or is no longer valid - log in again to continue.",
        ) from exc


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This action needs an account - log in first.",
        )
    payload = _decode_token(credentials.credentials)
    user = await session.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That account no longer exists - log in again with a current one.",
        )
    return user


async def get_optional_user(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = _decode_token(credentials.credentials)
    except HTTPException:
        return None
    return await session.get(User, payload.get("sub"))

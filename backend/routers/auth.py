from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import User, get_session
from backend.models.schemas import AuthOut, LoginIn, RegisterIn, UserOut
from backend.utils import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _normalised_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, session: AsyncSession = Depends(get_session)):
    email = _normalised_email(payload.email)
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for that email - log in instead, or use a different address.",
        )

    password_hash, salt = auth.hash_password(payload.password)
    user = User(name=payload.name.strip(), email=email, password_hash=password_hash, password_salt=salt)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return AuthOut(token=auth.create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthOut)
async def login(payload: LoginIn, session: AsyncSession = Depends(get_session)):
    email = _normalised_email(payload.email)
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or not auth.verify_password(payload.password, password_hash=user.password_hash, salt=user.password_salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That email and password combination doesn't match an account - check both and try again.",
        )

    return AuthOut(token=auth.create_access_token(user.id), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(auth.get_current_user)):
    return UserOut.model_validate(current_user)

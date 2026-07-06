from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.application.interfaces.user import IUserRepository
from app.core.settings import settings
from app.infrastructure.dependencies import get_user_repo

bearer_scheme = HTTPBearer(auto_error=False)


def _create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int, email: str):
    return _create_token(
        {"sub": user_id, "email": email, "type": "access"},
        timedelta(minutes=settings.ACCESS_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int, email: str):
    token = _create_token(
        {"sub": user_id, "email": email, "type": "refresh"},
        timedelta(days=settings.REFRESH_EXPIRE_DAYS),
    )
    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_EXPIRE_DAYS)
    return token, expires_at


def decode_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    repo: IUserRepository = Depends(get_user_repo),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing token")

    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Not an access token")

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid sub in token")

    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

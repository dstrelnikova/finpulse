from datetime import UTC, datetime
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt

from app.application.interfaces.user import IUserRepository
from app.application.use_cases.auth.login import Login
from app.application.use_cases.auth.register import Register
from app.core.settings import settings
from app.infrastructure.dependencies import get_user_repo
from app.infrastructure.security.auth_jwt import (
    create_access_token,
    create_refresh_token,
    get_current_user,
)
from app.presentation.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut
from app.presentation.schemas.users import UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])
_AUTH_ATTEMPTS: dict[str, list[float]] = {}
_AUTH_WINDOW_SEC = 5 * 60
_AUTH_MAX_ATTEMPTS = 20


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _rate_limit_auth(request: Request, key: str) -> None:
    now = time.monotonic()
    client_host = request.client.host if request.client else "unknown"
    bucket = f"{client_host}:{key.lower()}"
    attempts = [ts for ts in _AUTH_ATTEMPTS.get(bucket, []) if now - ts < _AUTH_WINDOW_SEC]
    if len(attempts) >= _AUTH_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many auth attempts")
    attempts.append(now)
    _AUTH_ATTEMPTS[bucket] = attempts


@router.post("/register", response_model=UserOut)
def register_user(
    data: RegisterIn,
    request: Request,
    repo: IUserRepository = Depends(get_user_repo),
):
    _rate_limit_auth(request, data.email)
    use_case = Register(repo)

    try:
        user = use_case.execute(
            name=data.name,
            email=data.email,
            password=data.password,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenOut)
def login_user(
    data: LoginIn,
    request: Request,
    repo: IUserRepository = Depends(get_user_repo),
):
    _rate_limit_auth(request, data.email)
    use_case = Login(repo)
    user = use_case.execute(email=data.email, password=data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(user.id, user.email)
    refresh_token, refresh_expires_at = create_refresh_token(user.id, user.email)

    repo.update_refresh_token(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=refresh_expires_at,
    )

    return TokenOut(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenOut)
def refresh_tokens(
    data: RefreshIn,
    request: Request,
    repo: IUserRepository = Depends(get_user_repo),
):
    _rate_limit_auth(request, data.refresh_token[:16])
    user = repo.get_by_refresh_token(data.refresh_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if not user.refresh_token_expires_at or _to_utc(user.refresh_token_expires_at) < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    try:
        payload = jwt.decode(
            data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    access_token = create_access_token(user.id, user.email)
    new_refresh_token, new_expires_at = create_refresh_token(user.id, user.email)

    repo.update_refresh_token(
        user_id=user.id,
        refresh_token=new_refresh_token,
        expires_at=new_expires_at,
    )

    return TokenOut(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
def logout_user(
    current_user=Depends(get_current_user),
    repo: IUserRepository = Depends(get_user_repo),
):
    repo.update_refresh_token(
        user_id=current_user.id,
        refresh_token=None,
        expires_at=None,
    )
    return {"detail": "Logged out"}

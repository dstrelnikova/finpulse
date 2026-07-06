from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
import os
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure settings can be initialized in tests without relying on local .env location.
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_EXPIRE_DAYS", "7")
os.environ.setdefault("OLLAMA_URL", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "stub")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")

from app.core.constants import MARKET_RU  # noqa: E402
from app.domain.entities.news_block import NewsBlock, NewsIndicator  # noqa: E402
from app.domain.entities.user import User  # noqa: E402
from app.infrastructure.dependencies import (  # noqa: E402
    get_chat_session_repo,
    get_moex_service,
    get_public_news_feed_use_case,
    get_public_news_item_by_slug_use_case,
    get_public_news_item_use_case,
    get_user_repo,
)
from app.infrastructure.security.auth_jwt import create_access_token  # noqa: E402
from app.presentation.api.admin_users import router as admin_users_router  # noqa: E402
from app.presentation.api.auth import router as auth_router  # noqa: E402
from app.presentation.api.me import router as me_router  # noqa: E402
from app.presentation.api.meta import router as meta_router  # noqa: E402
from app.presentation.api.public_moex import router as public_moex_router  # noqa: E402
from app.presentation.api.public_news import router as public_news_router  # noqa: E402

ROLE_PERMS = {
    "user": [
        "news:list",
        "news:read",
        "chat:use",
        "chat:history_read",
        "profile:read_own",
        "profile:update_own",
    ],
    "pro": [
        "news:list",
        "news:read",
        "chat:use",
        "chat:history_read",
        "profile:read_own",
        "profile:update_own",
    ],
    "admin": [
        "news:list",
        "news:read",
        "chat:use",
        "chat:history_read",
        "profile:read_own",
        "profile:update_own",
        "admin_users:assign_role",
        "admin_users:list",
    ],
}


class InMemoryUserRepo:
    def __init__(self) -> None:
        self._id_seq = 0
        self._users: dict[int, User] = {}
        self._roles: dict[int, set[str]] = {}
        self._refresh: dict[int, tuple[str | None, datetime | None]] = {}
        self._created_at: dict[int, datetime] = {}

    def create(self, user: User) -> User:
        self._id_seq += 1
        new_user = replace(user)
        new_user.id = self._id_seq
        self._users[new_user.id] = new_user
        self._created_at[new_user.id] = datetime.now(timezone.utc)
        self._roles.setdefault(new_user.id, set())
        self._refresh.setdefault(new_user.id, (None, None))
        return replace(new_user)

    def get_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email == email:
                return replace(user)
        return None

    def get_by_id(self, id: int) -> User | None:
        user = self._users.get(id)
        return replace(user) if user else None

    def delete(self, id: int) -> bool:
        if id not in self._users:
            return False
        self._users.pop(id, None)
        self._roles.pop(id, None)
        self._refresh.pop(id, None)
        self._created_at.pop(id, None)
        return True

    def update(self, user: User) -> User:
        if user.id is None or user.id not in self._users:
            raise ValueError("User not found")
        self._users[user.id] = replace(user)
        return replace(user)

    def get_roles(self, user_id: int) -> set[str]:
        return set(self._roles.get(user_id, set()))

    def get_permissions(self, user_id: int) -> set[str]:
        roles = self.get_roles(user_id)
        perms: set[str] = set()
        for role in roles:
            perms.update(ROLE_PERMS.get(role, []))
        return perms

    def set_roles(self, user_id: int, role_names: list[str]) -> set[str]:
        if user_id not in self._users:
            raise ValueError("User not found")
        allowed = set(ROLE_PERMS.keys())
        if any(role not in allowed for role in role_names):
            raise ValueError("Unknown role in request")
        self._roles[user_id] = set(role_names)
        return set(role_names)

    def update_refresh_token(self, user_id: int, refresh_token: str | None, expires_at: datetime | None):
        if user_id not in self._users:
            return
        self._refresh[user_id] = (refresh_token, expires_at)

    def get_by_refresh_token(self, refresh_token: str):
        for user_id, (token, expires_at) in self._refresh.items():
            if token == refresh_token:
                user = self._users[user_id]
                return SimpleNamespace(
                    id=user.id,
                    email=user.email,
                    refresh_token=token,
                    refresh_token_expires_at=expires_at,
                )
        return None

    def list_admin_users(self, q, role, sort_by, sort_dir, page, page_size):
        rows = []
        for user_id, user in self._users.items():
            user_roles = sorted(self._roles.get(user_id, set()))
            rows.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "roles": user_roles,
                    "created_at": self._created_at[user_id],
                }
            )

        if q:
            q_l = q.lower()
            rows = [r for r in rows if q_l in (r["email"] or "").lower() or q_l in (r["name"] or "").lower()]
        if role:
            rows = [r for r in rows if role in r["roles"]]

        def _role_sort_value(item: dict) -> str:
            return item["roles"][0] if item["roles"] else ""

        sort_map = {
            "created_at": lambda x: x["created_at"],
            "email": lambda x: x["email"],
            "role": _role_sort_value,
        }
        key_fn = sort_map.get(sort_by, sort_map["created_at"])
        rows.sort(key=key_fn, reverse=(sort_dir == "desc"))

        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        return rows[start:end], total


class InMemoryChatSessionRepo:
    def __init__(self) -> None:
        self._id_seq = 0
        self._chats: dict[int, SimpleNamespace] = {}

    def get_or_create_default(self, user_id: int):
        for c in self._chats.values():
            if c.owner_id == user_id and c.is_default:
                return c
        self._id_seq += 1
        c = SimpleNamespace(id=self._id_seq, owner_id=user_id, title="Основной", topic=None, is_default=True)
        self._chats[c.id] = c
        return c

    def ensure_owner(self, chat_id: int, user_id: int) -> None:
        c = self._chats.get(chat_id)
        if not c or c.owner_id != user_id:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="CHAT_NOT_FOUND")

    def create_chat(self, user_id: int, title: str, topic: str | None):
        self._id_seq += 1
        c = SimpleNamespace(id=self._id_seq, owner_id=user_id, title=title, topic=topic, is_default=False)
        self._chats[c.id] = c
        return c


class FakePublicNewsFeedUseCase:
    def execute(self, limit: int = 50, force: bool = False):
        del force
        base = NewsBlock(
            id="1",
            slug="market-brief",
            title="Market brief",
            source="test-source",
            url="https://example.com/news/1",
            summary="short summary",
            bullets=["fact 1", "fact 2"],
            conclusion="conclusion",
            risks=["risk 1"],
            indicator=NewsIndicator(impact="neutral", confidence="medium", rationale=["reason"]),
            asof=datetime.now(timezone.utc).date(),
        )
        return [base][: max(1, min(limit, 100))]


class FakePublicNewsItemUseCase:
    def execute(self, news_id: int):
        if news_id != 1:
            return None
        return FakePublicNewsFeedUseCase().execute(limit=1)[0]


class FakePublicNewsBySlugUseCase:
    def execute(self, slug: str):
        if slug != "market-brief":
            return None
        return FakePublicNewsFeedUseCase().execute(limit=1)[0]


class FakeMoexService:
    def __init__(self) -> None:
        self.called_limit: int | None = None

    def get_imoex_quotes(self, limit: int = 12):
        self.called_limit = limit
        now_iso = datetime.now(timezone.utc).isoformat()
        return {
            "index": "IMOEX",
            "source": "MOEX ISS",
            "fetched_at": now_iso,
            "fallback": False,
            "items": [
                {
                    "ticker": "SBER",
                    "short_name": "Sber",
                    "last": 300.0,
                    "change": 1.2,
                    "change_percent": 0.4,
                    "update_time": "12:00:00",
                }
                for _ in range(limit)
            ],
        }


@pytest.fixture
def fake_user_repo() -> InMemoryUserRepo:
    repo = InMemoryUserRepo()
    user = repo.create(
        User(
            id=None,
            name="User",
            email="user@example.com",
            password_hash="hash",
            market=MARKET_RU,
        )
    )
    repo.set_roles(user.id, ["user"])

    pro = repo.create(
        User(
            id=None,
            name="Pro",
            email="pro@example.com",
            password_hash="hash",
            market=MARKET_RU,
        )
    )
    repo.set_roles(pro.id, ["pro"])

    admin = repo.create(
        User(
            id=None,
            name="Admin",
            email="admin@example.com",
            password_hash="hash",
            market=MARKET_RU,
        )
    )
    repo.set_roles(admin.id, ["admin"])
    return repo


@pytest.fixture
def fake_chat_repo(fake_user_repo: InMemoryUserRepo) -> InMemoryChatSessionRepo:
    repo = InMemoryChatSessionRepo()
    for user_id in list(fake_user_repo._users.keys()):
        repo.get_or_create_default(user_id)
    return repo


@pytest.fixture
def fake_moex_service() -> FakeMoexService:
    return FakeMoexService()


@pytest.fixture
def test_app(fake_user_repo, fake_chat_repo, fake_moex_service) -> FastAPI:
    app = FastAPI(title="FinPulse Test API")
    app.include_router(auth_router)
    app.include_router(me_router)
    app.include_router(admin_users_router)
    app.include_router(meta_router)
    app.include_router(public_moex_router)
    app.include_router(public_news_router)

    app.dependency_overrides[get_user_repo] = lambda: fake_user_repo
    app.dependency_overrides[get_chat_session_repo] = lambda: fake_chat_repo
    app.dependency_overrides[get_moex_service] = lambda: fake_moex_service
    app.dependency_overrides[get_public_news_feed_use_case] = lambda: FakePublicNewsFeedUseCase()
    app.dependency_overrides[get_public_news_item_use_case] = lambda: FakePublicNewsItemUseCase()
    app.dependency_overrides[get_public_news_item_by_slug_use_case] = lambda: FakePublicNewsBySlugUseCase()

    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def auth_headers_for(fake_user_repo: InMemoryUserRepo):
    def _factory(email: str) -> dict[str, str]:
        user = fake_user_repo.get_by_email(email)
        assert user is not None
        token = create_access_token(user.id, user.email)
        return {"Authorization": f"Bearer {token}"}

    return _factory


@pytest.fixture
def future_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=7)


@pytest.fixture
def past_expiry() -> datetime:
    return datetime.now(UTC) - timedelta(days=1)

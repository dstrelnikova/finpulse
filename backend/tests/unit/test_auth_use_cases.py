from hashlib import sha256

import pytest

from app.application.use_cases.auth.login import Login
from app.application.use_cases.auth.register import Register
from app.core.constants import MARKET_RU
from app.domain.entities.user import User
from app.infrastructure.security.passwords import verify_password


class StubRepo:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._roles: dict[int, set[str]] = {}
        self._id = 0

    def create(self, user: User) -> User:
        self._id += 1
        user.id = self._id
        self._users[user.email] = user
        return user

    def get_by_email(self, email: str):
        return self._users.get(email)

    def set_roles(self, user_id: int, role_names: list[str]):
        self._roles[user_id] = set(role_names)
        return set(role_names)


@pytest.mark.unit
def test_login_returns_user_when_password_hash_matches():
    repo = StubRepo()
    pwd = "secret123"
    user = User(id=1, name="A", email="a@x.com", password_hash=sha256(pwd.encode()).hexdigest(), market=MARKET_RU)
    repo._users[user.email] = user

    result = Login(repo).execute(email=user.email, password=pwd)
    assert result is not None
    assert result.email == user.email


@pytest.mark.unit
def test_login_returns_none_for_wrong_password():
    repo = StubRepo()
    repo._users["a@x.com"] = User(
        id=1,
        name="A",
        email="a@x.com",
        password_hash=sha256("right".encode()).hexdigest(),
        market=MARKET_RU,
    )

    assert Login(repo).execute(email="a@x.com", password="wrong") is None


@pytest.mark.unit
def test_register_creates_user_and_assigns_default_role():
    repo = StubRepo()

    user = Register(repo).execute(name="Alice", email="alice@example.com", password="123456")

    assert user.id is not None
    assert user.market == MARKET_RU
    assert user.password_hash != sha256("123456".encode()).hexdigest()
    assert verify_password("123456", user.password_hash)
    assert repo._roles[user.id] == {"user"}


@pytest.mark.unit
def test_register_raises_for_duplicate_email():
    repo = StubRepo()
    repo._users["dup@example.com"] = User(
        id=1,
        name="Dup",
        email="dup@example.com",
        password_hash="x",
        market=MARKET_RU,
    )

    with pytest.raises(ValueError, match="User already exists"):
        Register(repo).execute(name="Dup", email="dup@example.com", password="123456")

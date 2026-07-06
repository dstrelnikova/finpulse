from app.application.interfaces.user import IUserRepository
from app.core.constants import MARKET_RU
from app.domain.entities.user import User
from app.infrastructure.security.passwords import hash_password


class Register:
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    def execute(
        self,
        name: str,
        email: str,
        password: str,
    ) -> User:
        if self.repo.get_by_email(email):
            raise ValueError("User already exists")

        user = User(
            id=None,
            name=name,
            email=email,
            password_hash=hash_password(password),
            market=MARKET_RU,
            investment_horizon=None,
            experience_level=None,
            risk_level=None,
            tickers=[],
            sectors=[],
        )
        user = self.repo.create(user)
        self.repo.set_roles(user.id, ["user"])
        return user

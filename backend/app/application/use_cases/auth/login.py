from app.application.interfaces.user import IUserRepository
from app.domain.entities.user import User
from app.infrastructure.security.passwords import verify_password


class Login:
    def __init__(self, repo: IUserRepository):
        self.repo = repo

    def execute(self, email: str, password: str) -> User | None:
        """Проверка email и пароля. Возвращает User или None."""
        user = self.repo.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

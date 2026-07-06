from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from app.domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[User]: ...

    @abstractmethod
    def delete(self, id: int) -> bool: ...

    def update(self, user: User) -> User: ...

    def get_roles(self, user_id: int) -> set[str]: ...

    def get_permissions(self, user_id: int) -> set[str]: ...

    def set_roles(self, user_id: int, role_names: list[str]) -> set[str]: ...

    def update_refresh_token(
        self, user_id: int, refresh_token: str | None, expires_at: datetime | None
    ) -> None: ...

    def get_by_refresh_token(self, refresh_token: str) -> Any | None: ...

    def list_admin_users(
        self,
        q: str | None,
        role: str | None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

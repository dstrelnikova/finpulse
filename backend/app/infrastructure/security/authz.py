from fastapi import Depends, HTTPException, status

from app.application.interfaces.user import IUserRepository
from app.infrastructure.dependencies import get_user_repo
from app.infrastructure.security.auth_jwt import get_current_user


def require_permissions(required: list[str]):
    required_set = set(required)

    def _dep(
        current_user=Depends(get_current_user),
        repo: IUserRepository = Depends(get_user_repo),
    ):
        perms = repo.get_permissions(current_user.id)
        if not required_set.issubset(perms):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return _dep

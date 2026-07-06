from fastapi import APIRouter, Depends

from app.application.interfaces.user import IUserRepository
from app.infrastructure.dependencies import get_user_repo
from app.infrastructure.security.auth_jwt import get_current_user

router = APIRouter(prefix="/me", tags=["Me"])


@router.get("")
def me(
    current_user=Depends(get_current_user),
    repo: IUserRepository = Depends(get_user_repo),
):
    roles = sorted(repo.get_roles(current_user.id))
    perms = sorted(repo.get_permissions(current_user.id))
    return {
        "id": current_user.id,
        "email": current_user.email,
        "roles": roles,
        "permissions": perms,
    }

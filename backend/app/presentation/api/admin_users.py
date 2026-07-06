from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.interfaces.user import IUserRepository
from app.infrastructure.dependencies import get_user_repo
from app.infrastructure.security.authz import require_permissions
from app.presentation.schemas.admin_users import PagedUsersOut, SetRolesIn

router = APIRouter(prefix="/admin/users", tags=["AdminUsers"])


@router.put(
    "/{user_id}/roles",
    dependencies=[Depends(require_permissions(["admin_users:assign_role"]))],
)
def set_roles(user_id: int, payload: SetRolesIn, repo: IUserRepository = Depends(get_user_repo)):
    try:
        roles = repo.set_roles(user_id, payload.roles)
        return {"user_id": user_id, "roles": sorted(roles)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=PagedUsersOut,
    dependencies=[Depends(require_permissions(["admin_users:list"]))],
)
def list_users(
    q: Optional[str] = Query(default=None, min_length=1, max_length=200),
    role: Optional[str] = Query(default=None, max_length=64),
    sort_by: Literal["created_at", "email", "role"] = Query(default="created_at"),
    sort_dir: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=100),
    repo: IUserRepository = Depends(get_user_repo),
):
    items, total = repo.list_admin_users(
        q=q,
        role=role,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}

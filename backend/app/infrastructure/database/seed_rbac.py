from sqlalchemy import text

from app.infrastructure.database.base import SessionLocal, engine
from app.infrastructure.database.models import PermissionModel, RoleModel, RolePermissionModel, UserModel, UserRoleModel

PERMISSIONS = [
    "news:list",
    "news:read",
    "chat:use",
    "chat:history_read",
    "profile:read_own",
    "profile:update_own",
    "admin_users:assign_role",
    "admin_users:list",
]

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


def ensure_user_subscription_column():
    with engine.begin() as conn:
        conn.execute(
            text(
                """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR NOT NULL DEFAULT 'free'
        """
            )
        )


def seed_rbac(admin_email: str | None = None):
    ensure_user_subscription_column()

    with SessionLocal() as session:
        roles_by_name = {r.name: r for r in session.query(RoleModel).all()}
        for role_name in ROLE_PERMS.keys():
            if role_name not in roles_by_name:
                r = RoleModel(name=role_name)
                session.add(r)
                session.flush()
                roles_by_name[role_name] = r

        perms_by_key = {p.key: p for p in session.query(PermissionModel).all()}
        for key in PERMISSIONS:
            if key not in perms_by_key:
                p = PermissionModel(key=key)
                session.add(p)
                session.flush()
                perms_by_key[key] = p

        session.flush()

        for role_name, keys in ROLE_PERMS.items():
            role = roles_by_name[role_name]
            allowed_perm_ids = {perms_by_key[key].id for key in keys}
            session.query(RolePermissionModel).filter(
                RolePermissionModel.role_id == role.id,
                RolePermissionModel.permission_id.notin_(allowed_perm_ids),
            ).delete(synchronize_session=False)
            for key in keys:
                perm = perms_by_key[key]
                exists = session.query(RolePermissionModel).filter_by(role_id=role.id, permission_id=perm.id).first()
                if not exists:
                    session.add(RolePermissionModel(role_id=role.id, permission_id=perm.id))

        session.flush()

        user_role = roles_by_name["user"]
        users_without_roles = (
            session.query(UserModel)
            .outerjoin(UserRoleModel, UserRoleModel.user_id == UserModel.id)
            .filter(UserRoleModel.user_id.is_(None))
            .all()
        )
        for u in users_without_roles:
            session.add(UserRoleModel(user_id=u.id, role_id=user_role.id))

        if admin_email:
            admin_user = session.query(UserModel).filter(UserModel.email == admin_email).first()
            if admin_user:
                admin_role = roles_by_name["admin"]
                session.query(UserRoleModel).filter(UserRoleModel.user_id == admin_user.id).delete()
                session.add(UserRoleModel(user_id=admin_user.id, role_id=admin_role.id))

        session.commit()

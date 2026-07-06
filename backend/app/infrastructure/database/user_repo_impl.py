from datetime import datetime
from typing import Any, Optional

from sqlalchemy import distinct, func, or_
from sqlalchemy.orm import sessionmaker

from app.application.interfaces.user import IUserRepository
from app.domain.entities.user import User
from app.infrastructure.database.base import SessionLocal
from app.infrastructure.database.models import PermissionModel, RoleModel, RolePermissionModel, UserModel, UserRoleModel


class UserRepositorySQL(IUserRepository):
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self._session_factory = session_factory

    def create(self, user: User) -> User:
        with self._session_factory() as session:
            existing = session.query(UserModel).filter_by(email=user.email).first()
            if existing:
                raise ValueError("Пользователь с таким email уже существует")

            db_user = UserModel(
                name=user.name,
                email=user.email,
                password_hash=user.password_hash,
                market=user.market,
                investment_horizon=user.investment_horizon,
                experience_level=user.experience_level,
                risk_level=user.risk_level,
                tickers=user.tickers,
                sectors=user.sectors,
            )

            session.add(db_user)
            session.commit()
            session.refresh(db_user)

            user.id = db_user.id
            return user

    def get_by_email(self, email: str) -> Optional[User]:
        with self._session_factory() as session:
            db_user = session.query(UserModel).filter_by(email=email).first()
            if db_user is None:
                return None

            return self._to_domain(db_user)

    def get_by_id(self, id: int) -> Optional[User]:
        with self._session_factory() as session:
            db_user = session.query(UserModel).filter_by(id=id).first()
            if db_user is None:
                return None

            return self._to_domain(db_user)

    def delete(self, id: int) -> bool:
        with self._session_factory() as session:
            db_user = session.query(UserModel).filter_by(id=id).first()
            if db_user is None:
                return False

            session.delete(db_user)
            session.commit()
            return True

    def update(self, user: User) -> User:
        with self._session_factory() as session:
            db_user = session.query(UserModel).filter_by(id=user.id).first()
            if not db_user:
                raise ValueError("User not found")

            db_user.name = user.name
            db_user.email = user.email
            db_user.password_hash = user.password_hash

            db_user.market = user.market
            db_user.investment_horizon = user.investment_horizon
            db_user.experience_level = user.experience_level
            db_user.risk_level = user.risk_level
            db_user.tickers = user.tickers
            db_user.sectors = user.sectors

            session.commit()
            session.refresh(db_user)
            return user

    def update_refresh_token(
        self,
        user_id: int,
        refresh_token: str | None,
        expires_at: datetime | None,
    ):
        with self._session_factory() as session:
            db_user = session.query(UserModel).get(user_id)
            if not db_user:
                return
            db_user.refresh_token = refresh_token
            db_user.refresh_token_expires_at = expires_at
            session.commit()

    def get_by_refresh_token(self, refresh_token: str) -> UserModel | None:
        with self._session_factory() as session:
            return session.query(UserModel).filter(UserModel.refresh_token == refresh_token).first()

    @staticmethod
    def _to_domain(db_user: UserModel) -> User:
        return User(
            id=db_user.id,
            name=db_user.name,
            email=db_user.email,
            password_hash=db_user.password_hash,
            market=db_user.market,
            investment_horizon=db_user.investment_horizon,
            experience_level=db_user.experience_level,
            risk_level=db_user.risk_level,
            tickers=db_user.tickers or [],
            sectors=db_user.sectors or [],
        )

    def get_roles(self, user_id: int) -> set[str]:
        with self._session_factory() as session:
            rows = (
                session.query(RoleModel.name)
                .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
                .filter(UserRoleModel.user_id == user_id)
                .all()
            )
            return {r[0] for r in rows}

    def get_permissions(self, user_id: int) -> set[str]:
        with self._session_factory() as session:
            rows = (
                session.query(PermissionModel.key)
                .join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)
                .join(UserRoleModel, UserRoleModel.role_id == RolePermissionModel.role_id)
                .filter(UserRoleModel.user_id == user_id)
                .all()
            )
            return {r[0] for r in rows}

    def set_roles(self, user_id: int, role_names: list[str]) -> set[str]:
        role_names = list(dict.fromkeys(role_names))
        with self._session_factory() as session:
            user_exists = session.query(UserModel.id).filter(UserModel.id == user_id).first()
            if not user_exists:
                raise ValueError("User not found")

            roles = session.query(RoleModel).filter(RoleModel.name.in_(role_names)).all()
            if len(roles) != len(role_names):
                raise ValueError("Unknown role in request")

            # replace roles
            session.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).delete()
            for r in roles:
                session.add(UserRoleModel(user_id=user_id, role_id=r.id))

            session.commit()
            return {r.name for r in roles}

    def list_admin_users(
        self,
        q: str | None,
        role: str | None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Возвращает пользователей для админки:
        - items: [{id,email,name,roles,created_at}]
        - total: общее кол-во с учётом фильтров (без пагинации)
        """
        with self._session_factory() as session:
            roles_agg = func.array_remove(func.array_agg(func.distinct(RoleModel.name)), None).label("roles")
            role_sort = func.min(RoleModel.name).label("role_sort")

            base = (
                session.query(
                    UserModel.id.label("id"),
                    UserModel.email.label("email"),
                    UserModel.name.label("name"),
                    getattr(UserModel, "created_at", UserModel.id).label("created_at"),
                    roles_agg,
                    role_sort,
                )
                .outerjoin(UserRoleModel, UserRoleModel.user_id == UserModel.id)
                .outerjoin(RoleModel, RoleModel.id == UserRoleModel.role_id)
            )

            # Поиск
            if q:
                pattern = f"%{q.strip()}%"
                base = base.filter(
                    or_(
                        UserModel.email.ilike(pattern),
                        UserModel.name.ilike(pattern),
                    )
                )

            # Фильтр role
            if role:
                users_with_role = (
                    session.query(UserRoleModel.user_id)
                    .join(RoleModel, RoleModel.id == UserRoleModel.role_id)
                    .filter(RoleModel.name == role)
                )
                base = base.filter(UserModel.id.in_(users_with_role))

            base = base.group_by(UserModel.id)

            total_q = (
                session.query(func.count(distinct(UserModel.id)))
                .outerjoin(UserRoleModel, UserRoleModel.user_id == UserModel.id)
                .outerjoin(RoleModel, RoleModel.id == UserRoleModel.role_id)
            )
            if q:
                pattern = f"%{q.strip()}%"
                total_q = total_q.filter(or_(UserModel.email.ilike(pattern), UserModel.name.ilike(pattern)))
            if role:
                total_q = total_q.filter(RoleModel.name == role)

            total = int(total_q.scalar() or 0)

            # Сортировка
            sort_map = {
                "created_at": getattr(UserModel, "created_at", UserModel.id),
                "email": UserModel.email,
                "role": role_sort,
            }
            col = sort_map.get(sort_by, getattr(UserModel, "created_at", UserModel.id))
            ordering = col.asc() if sort_dir == "asc" else col.desc()
            base = base.order_by(ordering)

            # Пагинация
            base = base.offset((page - 1) * page_size).limit(page_size)

            rows = base.all()

            items: list[dict[str, Any]] = []
            for r in rows:
                roles = list(r.roles or [])
                roles.sort()
                items.append(
                    {
                        "id": r.id,
                        "email": r.email,
                        "name": r.name,
                        "created_at": r.created_at,
                        "roles": roles,
                    }
                )

            return items, total

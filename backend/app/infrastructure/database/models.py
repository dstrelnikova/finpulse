from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    Index,
)

from app.core.constants import MARKET_RU
from app.infrastructure.database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    market = Column(String, nullable=False, server_default=MARKET_RU)

    investment_horizon = Column(String, nullable=True)  # short | mid | long
    experience_level = Column(String, nullable=True)  # beginner | intermediate | pro
    risk_level = Column(String, nullable=True)  # low | medium | high

    tickers = Column(ARRAY(String), nullable=False, server_default="{}")
    sectors = Column(ARRAY(String), nullable=False, server_default="{}")

    refresh_token = Column(String, nullable=True)
    refresh_token_expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    chat_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (CheckConstraint("role IN ('user', 'FinPulse')", name="chat_messages_role_check"),)


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(120), nullable=False)
    topic = Column(String(120), nullable=True)
    is_default = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class NewsCacheModel(Base):
    __tablename__ = "news_cache"

    id = Column(Integer, primary_key=True, index=True)

    cache_date = Column(Date, nullable=False, index=True)
    market = Column(String, nullable=False)
    category = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)
    title = Column(String, nullable=False)

    payload_json = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("cache_date", "category", "url", name="uq_news_cache_day_cat_url"),)


class RoleModel(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # user|pro|admin


class PermissionModel(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)  # "chat:use"


class UserRoleModel(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_perm"),)


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)

    # Метаданные статьи
    title = Column(String(512), nullable=False)
    slug = Column(String(512), nullable=False, index=True)

    source = Column(String(256), nullable=False)
    url = Column(Text, nullable=False, unique=True)  # чтобы не дублировать одну статью

    # Дата (если у вас есть только date), можно хранить как asof
    asof = Column(Date, nullable=True)

    # Категоризация
    market = Column(String(64), nullable=True)
    category = Column(String(64), nullable=True, index=True)

    # Нормализованный payload суммаризации (JSON строкой)
    payload_json = Column(Text, nullable=False)

    # Публичность (для /public/news)
    is_public = Column(Boolean, nullable=False, server_default="true", index=True)

    # Технические поля
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Для быстрых выборок "последние публичные"
        Index("ix_news_public_created", "is_public", "created_at"),
    )

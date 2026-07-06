from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.base import SessionLocal
from app.infrastructure.database.models import ChatSessionModel


class ChatSessionRepositorySQL:
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self._session_factory = session_factory

    def get_or_create_default(self, user_id: int) -> ChatSessionModel:
        with self._session_factory() as session:
            chat = (
                session.query(ChatSessionModel)
                .filter(ChatSessionModel.owner_id == user_id, ChatSessionModel.is_default.is_(True))
                .first()
            )
            if chat:
                return chat

            chat = ChatSessionModel(owner_id=user_id, title="Основной", topic=None, is_default=True)
            session.add(chat)
            session.commit()
            session.refresh(chat)
            return chat

    def ensure_owner(self, chat_id: int, user_id: int) -> None:
        with self._session_factory() as session:
            ok = (
                session.query(ChatSessionModel.id)
                .filter(ChatSessionModel.id == chat_id, ChatSessionModel.owner_id == user_id)
                .first()
            )
            if not ok:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="CHAT_NOT_FOUND")

    def count_user_chats(self, user_id: int) -> int:
        with self._session_factory() as session:
            return int(
                session.query(func.count(ChatSessionModel.id)).filter(ChatSessionModel.owner_id == user_id).scalar()
                or 0
            )

    def list_user_chats(self, user_id: int):
        with self._session_factory() as session:
            return (
                session.query(ChatSessionModel)
                .filter(ChatSessionModel.owner_id == user_id)
                .order_by(ChatSessionModel.updated_at.desc())
                .all()
            )

    def create_chat(self, user_id: int, title: str, topic: str | None):
        with self._session_factory() as session:
            chat = ChatSessionModel(owner_id=user_id, title=title, topic=topic, is_default=False)
            session.add(chat)
            session.commit()
            session.refresh(chat)
            return chat

    def delete_chat(self, user_id: int, chat_id: int):
        with self._session_factory() as session:
            chat = (
                session.query(ChatSessionModel)
                .filter(ChatSessionModel.id == chat_id, ChatSessionModel.owner_id == user_id)
                .first()
            )
            if not chat:
                return False

            # безопасно: не даём удалить default-чат
            if getattr(chat, "is_default", False):
                raise ValueError("CANNOT_DELETE_DEFAULT_CHAT")

            session.delete(chat)
            session.commit()
            return True

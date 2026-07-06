from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import sessionmaker

from app.domain.entities.chat_message import ChatMessage
from app.infrastructure.database.base import SessionLocal
from app.infrastructure.database.models import ChatMessageModel, ChatSessionModel


class ChatRepositorySQL:
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        self._session_factory = session_factory

    def _get_or_create_default_chat_id(self, session, user_id: int) -> int:
        chat = (
            session.query(ChatSessionModel)
            .filter(ChatSessionModel.owner_id == user_id, ChatSessionModel.is_default.is_(True))
            .first()
        )
        if chat:
            return chat.id

        chat = ChatSessionModel(
            owner_id=user_id,
            title="Main",
            topic=None,
            is_default=True,
        )
        session.add(chat)
        session.flush()  # получить chat.id без commit
        return chat.id

    def add_message(self, message: ChatMessage, chat_id: Optional[int] = None) -> ChatMessage:
        with self._session_factory() as session:
            # если chat_id не передали — пишем в default чат пользователя
            effective_chat_id = chat_id or getattr(message, "chat_id", None)
            if effective_chat_id is None:
                effective_chat_id = self._get_or_create_default_chat_id(session, message.user_id)

            db_msg = ChatMessageModel(
                user_id=message.user_id,
                chat_id=effective_chat_id,
                role=message.role,
                content=message.content,
                timestamp=message.timestamp or datetime.utcnow(),
            )
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)

            message.id = db_msg.id
            message.chat_id = db_msg.chat_id
            return message

    def get_last_messages(
        self,
        user_id: int,
        limit: int = 20,
        chat_id: Optional[int] = None,
    ) -> List[ChatMessage]:
        """
        Возвращает последние N сообщений в рамках одного чата.
        Если chat_id не задан — берём default чат пользователя.
        """
        with self._session_factory() as session:
            effective_chat_id = chat_id
            if effective_chat_id is None:
                effective_chat_id = self._get_or_create_default_chat_id(session, user_id)

            rows = (
                session.query(ChatMessageModel)
                .filter(
                    ChatMessageModel.user_id == user_id,
                    ChatMessageModel.chat_id == effective_chat_id,
                )
                .order_by(ChatMessageModel.timestamp.desc())
                .limit(limit)
                .all()
            )

            rows = list(reversed(rows))

            return [
                ChatMessage(
                    id=row.id,
                    user_id=row.user_id,
                    chat_id=row.chat_id,
                    role=row.role,
                    content=row.content,
                    timestamp=row.timestamp,
                )
                for row in rows
            ]

    def clear_messages(self, user_id: int, chat_id: Optional[int] = None) -> int:
        with self._session_factory() as session:
            effective_chat_id = chat_id
            if effective_chat_id is None:
                effective_chat_id = self._get_or_create_default_chat_id(session, user_id)

            deleted = (
                session.query(ChatMessageModel)
                .filter(
                    ChatMessageModel.user_id == user_id,
                    ChatMessageModel.chat_id == effective_chat_id,
                )
                .delete(synchronize_session=False)
            )
            session.commit()
            return int(deleted)

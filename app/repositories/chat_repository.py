from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chat import ChatMessage, ChatSession


class ChatRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_session(self) -> ChatSession:
        session = ChatSession()

        self.db.add(session)
        self.db.flush()

        return session

    def get_session(
        self,
        session_id: UUID,
    ) -> ChatSession | None:
        statement = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
        )

        return self.db.scalar(statement)

    def get_session_with_messages(
        self,
        session_id: UUID,
    ) -> ChatSession | None:
        statement = (
            select(ChatSession)
            .options(
                selectinload(ChatSession.messages)
            )
            .where(ChatSession.id == session_id)
        )

        return self.db.scalar(statement)

    def add_message(
        self,
        session: ChatSession,
        role: str,
        content: str,
    ) -> ChatMessage:
        message = ChatMessage(
            session=session,
            role=role,
            content=content,
        )

        self.db.add(message)
        self.db.flush()

        return message

    def save(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
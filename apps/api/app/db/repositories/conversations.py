from collections.abc import Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import Repository
from app.models import Conversation, Message, User


class ConversationRepository(Repository[Conversation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Conversation)

    async def ensure_user(self, user_id: str, email: str | None = None) -> User:
        user = await self.session.get(User, user_id)
        if user:
            return user
        user = User(id=user_id, email=email, name=email or "Local user")
        self.session.add(user)
        await self.session.flush()
        return user

    async def list_for_user(self, user_id: str, query: str | None = None) -> Sequence[Conversation]:
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.archived.is_(False))
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.pinned.desc(), Conversation.updated_at.desc())
        )
        if query:
            like = f"%{query}%"
            statement = statement.where(Conversation.title.ilike(like))
        result = await self.session.scalars(statement)
        return result.unique().all()

    async def get_for_user(self, conversation_id: str, user_id: str) -> Conversation | None:
        statement = (
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        return await self.session.scalar(statement)

    async def create(self, user_id: str, title: str = "New conversation") -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: list | None = None,
        metadata: dict | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            metadata_json=metadata or {},
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def edit_message(self, message_id: str, user_id: str, content: str) -> Message | None:
        statement = (
            select(Message)
            .join(Conversation)
            .where(Message.id == message_id, Conversation.user_id == user_id)
        )
        message = await self.session.scalar(statement)
        if not message:
            return None
        message.content = content
        message.metadata_json = {**message.metadata_json, "edited": True}
        await self.session.flush()
        return message

    async def search_messages(self, user_id: str, query: str) -> Sequence[Message]:
        like = f"%{query}%"
        statement = (
            select(Message)
            .join(Conversation)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.archived.is_(False),
                    or_(Message.content.ilike(like), Conversation.title.ilike(like)),
                )
            )
            .order_by(Message.updated_at.desc())
            .limit(50)
        )
        result = await self.session.scalars(statement)
        return result.all()

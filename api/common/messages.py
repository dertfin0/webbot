from common.database import Base, db
from sqlalchemy import BIGINT, VARCHAR, BOOLEAN, INTEGER, select
from sqlalchemy.orm import Mapped, mapped_column


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(VARCHAR(2048))
    by_bot: Mapped[bool] = mapped_column(BOOLEAN)
    handled: Mapped[bool] = mapped_column(BOOLEAN)
    sent_at: Mapped[int] = mapped_column(BIGINT)

async def save_message(message: Message) -> Message:
    async with db.Session() as session:
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message

async def get_messages_from_id(last_received_id: int) -> list:
    async with db.Session() as session:
        query = select(Message).where(Message.id > last_received_id)
        result = await session.execute(query)
        return result.scalars().all()
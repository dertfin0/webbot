from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


class Database:
    def __init__(self):
        self.engine = create_async_engine('sqlite+aiosqlite:///database.db', echo=False)
        self.Session = async_sessionmaker(bind=self.engine, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

db = Database()

async def init():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import config
from app.db.base import Base
from app.db.models import Application

engine = create_async_engine(config.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

db_url = settings.database_url
# Use SQLite for local dev if postgres isn't configured
if "postgresql" in db_url and "localhost" in db_url:
    db_url = "sqlite+aiosqlite:///./ex_venture.db"

engine_kwargs = {
    "echo": settings.debug,
    "future": True,
}
# Pool settings only for non-SQLite
if "sqlite" not in db_url:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_async_engine(db_url, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, future=True
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

"""
Safe database initialization script.
Creates tables if they don't exist (doesn't drop existing tables).
Safe for production use.
"""
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.models.database import Base
from app.core.config import settings


async def init_db_safe():
    """Create tables that don't exist yet (safe mode)."""
    print("🔄 Connecting to database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("✨ Creating tables (if they don't exist)...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Database ready!")


if __name__ == "__main__":
    asyncio.run(init_db_safe())

import asyncio
from database.database import init_db
from database.models import Organization, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def setup_database():
    """Инициализация базы данных и создание тестовой организации"""
    print("Инициализация базы данных...")
    await init_db()
    print("База данных инициализирована успешно!")


if __name__ == "__main__":
    asyncio.run(setup_database())
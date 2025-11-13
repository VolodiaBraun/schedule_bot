import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database.database import init_db

async def main():
    # Получение токена из переменной окружения
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise ValueError("Необходимо установить BOT_TOKEN в переменных окружения")
    
    # Создание диспетчера с хранилищем состояний
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация базы данных
    await init_db()
    
    # Создание бота
    bot = Bot(token=bot_token)
    
    # Регистрация хендлеров
    from handlers import admin_handlers, client_handlers
    dp.include_router(admin_handlers.router)
    dp.include_router(client_handlers.router)
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
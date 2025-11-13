# Рекомендации по использованию webhook вместо polling

## Преимущества webhook перед polling

1. Лучшая производительность
2. Меньше задержки в ответах
3. Экономия ресурсов сервера
4. Возможность масштабирования

## Настройка webhook в коде

Для перехода с long polling на webhook, замените вызов `dp.start_polling(bot)` в файле `main.py` на:

```python
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

    # Настройка webhook (замените YOUR_DOMAIN на ваш домен)
    webhook_url = "https://ваш_домен.com/webhook"
    await bot.set_webhook(webhook_url)
    
    # Запуск webhook
    await dp.start_webhook(bot, webhook_url)

if __name__ == "__main__":
    asyncio.run(main())
```

## Настройка сервера для webhook

### Для Flask-приложения:
```python
from flask import Flask, request
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Update

app = Flask(__name__)

# Инициализация бота и диспетчера (как в примере выше)
# ...

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.model_validate(request.json, context={'bot': bot})
    asyncio.create_task(dp.feed_update(bot, update))
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

### Для FastAPI-приложения:
```python
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update

app = FastAPI()

# Инициализация бота и диспетчера (как в примере выше)
# ...

@app.post('/webhook')
async def webhook_endpoint(request: Request):
    update = Update.model_validate(await request.json(), context={'bot': bot})
    asyncio.create_task(dp.feed_update(bot, update))
    return {'status': 'ok'}
```

## Настройка reverse proxy (nginx)

Для настройки HTTPS и правильной работы webhook, рекомендуется использовать nginx:

```
server {
    listen 443 ssl;
    server_name ваш_домен.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location /webhook {
        proxy_pass http://localhost:8000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Проверка webhook

После настройки webhook, можно проверить его статус:
```python
webhook_info = await bot.get_webhook_info()
print(webhook_info.url)
print(webhook_info.last_error_message)
```

## Восстановление polling для разработки

Если нужно вернуться к polling в процессе разработки:
```python
# Очистка webhook
await bot.delete_webhook()

# Запуск polling
await dp.start_polling(bot)
```
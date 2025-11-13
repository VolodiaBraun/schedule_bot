#!/usr/bin/python3
# Файл для запуска бота на PythonAnywhere
import sys
import os

# Добавляем путь к проекту
project_dir = '/home/ваше_имя_пользователя/mysite'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Загружаем переменные окружения
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

# Импортируем и запускаем бота
from main import main
import asyncio

def start_bot():
    """Функция для запуска бота"""
    try:
        # Запускаем main() как асинхронную функцию в отдельном потоке
        import threading
        def run_async_main():
            asyncio.run(main())
        
        bot_thread = threading.Thread(target=run_async_main, daemon=True)
        bot_thread.start()
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

# Запускаем бота при загрузке модуля
start_bot()

# Заглушка для WSGI-совместимости (если используется как веб-приложение)
def application(environ, start_response):
    status = '200 OK'
    output = b'Telegram Bot is running!'
    
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    
    return [output]
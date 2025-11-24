FROM python:3.11-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Установка рабочей директории в контейнере
WORKDIR /app

# Копирование файла зависимостей
COPY requirements_prod.txt /app/

# Установка зависимостей
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && pip install --upgrade pip \
    && pip install -r requirements_prod.txt \
    && rm -rf /root/.cache/pip

# Копирование исходного кода
COPY . /app/

# Создание директории для базы данных (если используется SQLite)
RUN mkdir -p /app/data

# Проверка работоспособности
RUN python -c "import aiogram, sqlalchemy, os, dotenv"

# Запуск приложения
CMD ["python", "main.py"]
#!/bin/bash

# Скрипт запуска Telegram-бота для записи "без окон"
# Автор: BMAD Method
# Назначение: запуск бота с правильной настройкой окружения

# Установка цветовых кодов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка, что скрипт запускается из правильной директории
if [ ! -f "main.py" ]; then
  echo -e "${RED}Ошибка: main.py не найден в текущей директории${NC}"
  echo "Убедитесь, что вы запускаете скрипт из директории BookingBot"
  exit 1
fi

echo -e "${GREEN}=== Запуск Telegram-бота для записи ===${NC}"

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Ошибка: python3 не установлен${NC}"
    exit 1
fi

# Проверка наличия pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}pip3 не найден, пытаемся установить...${NC}"
    sudo apt update
    sudo apt install python3-pip
fi

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Создание виртуального окружения...${NC}"
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env файл не найден, создайте его на основе .env.example${NC}"
    echo -e "${YELLOW}Копируем .env.example в .env...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Пожалуйста, обновите .env файл с вашими настройками${NC}"
fi

# Установка зависимостей
echo -e "${YELLOW}Установка зависимостей...${NC}"
pip3 install --upgrade pip
pip3 install -r requirements_prod.txt

# Инициализация базы данных
echo -e "${YELLOW}Инициализация базы данных...${NC}"
python3 setup_db.py

# Проверка переменной окружения BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    echo -e "${YELLOW}BOT_TOKEN не установлен в переменных окружения${NC}"
    # Загрузка переменных из .env файла
    if [ -f ".env" ]; then
        export $(cat .env | xargs)
        echo -e "${GREEN}Переменные окружения загружены из .env${NC}"
    fi
fi

# Проверка токена бота еще раз
if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "ваш_токен_бота_здесь" ]; then
    echo -e "${RED}Ошибка: BOT_TOKEN не установлен.${NC}"
    echo -e "${RED}Пожалуйста, установите BOT_TOKEN в .env файле.${NC}"
    exit 1
fi

echo -e "${GREEN}Все проверки пройдены. Запуск бота...${NC}"

# Запуск бота
python3 main.py

# Деактивация виртуального окружения при завершении
deactivate

echo -e "${GREEN}Бот остановлен${NC}"
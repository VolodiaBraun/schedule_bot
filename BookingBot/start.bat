@echo off
REM Скрипт запуска Telegram-бота для записи "без окон" (Windows версия)
REM Автор: BMAD Method
REM Назначение: запуск бота с правильной настройкой окружения

echo === Запуск Telegram-бота для записи (Windows) ===

REM Проверка, что скрипт запускается из правильной директории
if not exist "main.py" (
    echo Ошибка: main.py не найден в текущей директории
    echo Убедитесь, что вы запускаете скрипт из директории BookingBot
    pause
    exit /b 1
)

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: python не установлен или не найден в PATH
    pause
    exit /b 1
)

REM Проверка наличия pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo pip не найден, установка...
    python -m ensurepip --upgrade
)

REM Проверка наличия виртуального окружения
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активация виртуального окружения
call venv\Scripts\activate.bat

REM Проверка наличия .env файла
if not exist ".env" (
    echo .env файл не найден, копирование из .env.example...
    if exist ".env.example" (
        copy .env.example .env
        echo Пожалуйста, обновите .env файл с вашими настройками
    ) else (
        echo Файл .env.example также отсутствует
    )
)

REM Установка зависимостей
echo Установка зависимостей...
pip install --upgrade pip
if exist "requirements_prod.txt" (
    pip install -r requirements_prod.txt
) else (
    pip install -r requirements.txt
)

REM Инициализация базы данных
echo Инициализация базы данных...
python setup_db.py

REM Загрузка переменных из .env файла (ограниченная поддержка в Windows CMD)
for /f "tokens=*" %%i in ('findstr /b /c:"BOT_TOKEN" .env') do set %%i

REM Проверка токена бота
if "%BOT_TOKEN%"=="" (
    echo Ошибка: BOT_TOKEN не установлен в .env файле.
    echo Установите BOT_TOKEN в .env файле.
    pause
    exit /b 1
)

if "%BOT_TOKEN%"=="ваш_токен_бота_здесь" (
    echo Ошибка: Необходимо обновить BOT_TOKEN в .env файле.
    echo Установите действительный токен бота.
    pause
    exit /b 1
)

echo Все проверки пройдены. Запуск бота...
REM Запуск бота
python main.py

REM Показываем сообщение перед закрытием
echo Бот остановлен
pause
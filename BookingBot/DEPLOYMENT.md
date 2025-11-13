# Инструкции по развертыванию Telegram-бота

## Подготовка к развертыванию

1. Получите токен у @BotFather в Telegram
2. Обновите файл .env с вашим токеном:
   ```
   BOT_TOKEN=ваш_токен_здесь
   ```

## Варианты развертывания

### 1. PythonAnywhere (рекомендуется для начала)

1. Зарегистрируйтесь на https://www.pythonanywhere.com/
2. Создайте новый Bash-консоль
3. Склонируйте репозиторий или загрузите файлы
4. Создайте виртуальное окружение:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.9 booking_bot
   pip install -r requirements_simple.txt
   ```
5. Установите ваш токен в переменные окружения:
   - В разделе "Account" -> "Environment variables" добавьте:
     ```
     BOT_TOKEN = ваш_токен_здесь
     ```
6. Запустите бота:
   ```bash
   python main.py
   ```

### 2. Railway

1. Создайте аккаунт на https://railway.app/
2. Создайте новый проект
3. Свяжите с GitHub репозиторий
4. В настройках добавьте переменную окружения:
   - Key: `BOT_TOKEN`, Value: ваш_токен_здесь
5. Деплой будет выполнен автоматически

### 3. VPS (продвинутый вариант)

1. Настройте сервер (Ubuntu/Debian рекомендуется)
2. Установите Python 3.9+, pip
3. Клонируйте репозиторий
4. Установите зависимости:
   ```bash
   pip install -r requirements_simple.txt
   ```
5. Настройте systemd-сервис:
   Создайте файл `/etc/systemd/system/booking_bot.service`:
   ```
   [Unit]
   Description=Telegram Booking Bot
   After=network.target

   [Service]
   Type=simple
   User=пользователь
   WorkingDirectory=/путь/к/боту
   ExecStart=/путь/к/виртуальному/окружению/bin/python main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
6. Запустите сервис:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable booking_bot
   sudo systemctl start booking_bot
   ```

## Настройка базы данных

Бот по умолчанию использует SQLite. Для более надежного хранения данных рекомендуется использовать PostgreSQL:

### Для Railway:
- Добавьте плагин PostgreSQL к проекту
- В переменных окружения укажите:
  ```
  DATABASE_URL=postgresql://username:password@host:port/dbname
  ```

### Для PythonAnywhere:
- Зайдите во вкладку Databases
- Создайте новую базу данных
- В переменных окружения укажите:
  ```
  DATABASE_URL=postgresql://username:password@localhost/dbname
  ```

## Запуск инициализации базы данных

Перед первым запуском бота выполните:
```bash
python setup_db.py
```

## Тестирование

После запуска бота, проверьте его работу, отправив ему команду `/start` в Telegram.
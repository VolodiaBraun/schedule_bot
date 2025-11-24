# Установка и запуск бота на VPS

## Подготовка VPS

1. Обновите систему:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Установите необходимые пакеты:
```bash
sudo apt install python3 python3-pip python3-venv git postgresql postgresql-contrib curl wget -y
```

3. Установите Docker (опционально, но рекомендуется):
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
```

4. Установите docker-compose:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Способ 1: Запуск с помощью Docker Compose (рекомендуется)

1. Склонируйте репозиторий:
```bash
git clone https://github.com/ваш-репозиторий/booking-bot.git
cd booking-bot/BookingBot
```

2. Скопируйте и отредактируйте .env файл:
```bash
cp .env.example .env
nano .env
```

3. Заполните .env файл вашим токеном бота:
```env
BOT_TOKEN=ваш_токен_бота_здесь
```

4. Запустите сервисы:
```bash
docker-compose up -d
```

## Способ 2: Запуск без Docker

1. Склонируйте репозиторий:
```bash
git clone https://github.com/ваш-репозиторий/booking-bot.git
cd booking-bot/BookingBot
```

2. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install --upgrade pip
pip install -r requirements_prod.txt
```

4. Скопируйте и отредактируйте .env файл:
```bash
cp .env.example .env
nano .env
```

5. Заполните .env файл вашим токеном бота:
```env
BOT_TOKEN=ваш_токен_бота_здесь
```

6. Инициализируйте базу данных:
```bash
python setup_db.py
```

7. Запустите бота:
```bash
python main.py
```

## Запуск в фоновом режиме

Для постоянной работы бота на VPS используйте один из следующих способов:

### С использованием screen:
```bash
screen -S booking_bot
python main.py
# Нажмите Ctrl+A, затем D чтобы открепиться от сессии
```

### С использованием systemd (рекомендуется):

1. Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/booking-bot.service
```

2. Добавьте следующее содержимое (обновите пути к файлам по необходимости):
```ini
[Unit]
Description=Booking Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/booking-bot/BookingBot
EnvironmentFile=/home/$USER/booking-bot/BookingBot/.env
ExecStart=/home/$USER/booking-bot/BookingBot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Перезапустите systemd daemon и включите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable booking-bot
sudo systemctl start booking-bot
```

4. Проверьте статус сервиса:
```bash
sudo systemctl status booking-bot
```

## Мониторинг и логирование

Для просмотра логов с использованием systemd:
```bash
sudo journalctl -u booking-bot -f
```

## Обновление бота

1. Остановите сервис:
```bash
sudo systemctl stop booking-bot  # для systemd
# или
# docker-compose down  # для Docker
```

2. Обновите код:
```bash
git pull origin main
```

3. Обновите зависимости (если использовался способ без Docker):
```bash
source venv/bin/activate
pip install -r requirements_prod.txt
```

4. Запустите сервис снова:
```bash
sudo systemctl start booking-bot  # для systemd
# или
# docker-compose up -d  # для Docker
```

## Устранение неполадок

### Если бот не запускается:
- Проверьте, что токен бота указан правильно в .env файле
- Убедитесь, что все зависимости установлены
- Проверьте логи для выявления ошибок

### Если возникают ошибки с базой данных:
- Убедитесь, что PostgreSQL запущен и доступен
- Проверьте настройки подключения в DATABASE_URL
- Убедитесь, что у пользователя PostgreSQL есть необходимые права

### Если бот не отвечает:
- Проверьте, что бот не заблокирован в Telegram
- Убедитесь, что сеть и соединение с Telegram API работают корректно
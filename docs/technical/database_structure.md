# Структура базы данных для Telegram-бота для записи без "окон"

## 8.1 Общие положения

Система должна использовать реляционную базу данных (предпочтительно PostgreSQL или SQLite) для хранения информации о расписании, записях, пользователях и настройках.

## 8.2 Таблицы базы данных

### 8.2.1 Таблица "administrators" - информация об администраторах
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT) - уникальный идентификатор администратора
- telegram_id (BIGINT, UNIQUE) - Telegram ID администратора
- username (TEXT) - имя пользователя в Telegram (опционально)
- full_name (TEXT) - полное имя администратора
- created_at (TIMESTAMP) - дата создания записи

### 8.2.2 Таблица "schedules" - расписание работы
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT) - уникальный идентификатор расписания
- day_of_week (INTEGER) - день недели (0 - воскресенье, 1 - понедельник, ..., 6 - суббота)
- start_time (TIME) - время начала работы (например, 16:00:00)
- end_time (TIME) - время окончания работы (например, 20:00:00)
- max_sessions_per_day (INTEGER) - максимальное количество сеансов в день
- session_duration (INTEGER) - длительность сеанса в минутах (по умолчанию 60)
- is_active (BOOLEAN) - активно ли расписание (для отключения на определенные дни)
- created_at (TIMESTAMP) - дата создания записи
- updated_at (TIMESTAMP) - дата последнего обновления

### 8.2.3 Таблица "specific_dates" - исключения для конкретных дат
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT) - уникальный идентификатор исключения
- date (DATE) - конкретная дата
- start_time (TIME) - время начала работы в этот день (если NULL, то выходной)
- end_time (TIME) - время окончания работы в этот день
- max_sessions_per_day (INTEGER) - максимальное количество сеансов в этот день (если NULL, использовать по умолчанию)
- is_exception (BOOLEAN) - является ли это исключением из основного расписания
- created_at (TIMESTAMP) - дата создания записи

### 8.2.4 Таблица "bookings" - записи клиентов
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT) - уникальный идентификатор записи
- telegram_user_id (BIGINT) - Telegram ID клиента
- user_full_name (TEXT) - полное имя клиента
- booking_date (DATE) - дата записи
- start_time (TIME) - время начала сеанса
- end_time (TIME) - время окончания сеанса (вычисляется на основе длительности)
- booking_status (TEXT) - статус записи (active, cancelled, completed)
- created_at (TIMESTAMP) - дата создания записи
- updated_at (TIMESTAMP) - дата последнего обновления
- cancelled_at (TIMESTAMP) - дата отмены (если была отменена)

### 8.2.5 Таблица "users" - информация о пользователях
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT) - уникальный идентификатор пользователя
- telegram_id (BIGINT, UNIQUE) - Telegram ID пользователя
- username (TEXT) - имя пользователя в Telegram
- full_name (TEXT) - полное имя пользователя
- created_at (TIMESTAMP) - дата регистрации пользователя
- last_interaction_at (TIMESTAMP) - дата последнего взаимодействия

### 8.2.6 Таблица "settings" - настройки системы
- id (INTEGER, PRIMARY KEY, AUTOINCREMENT) - уникальный идентификатор настройки
- setting_key (TEXT, UNIQUE) - ключ настройки (например, 'default_session_duration', 'admin_telegram_id')
- setting_value (TEXT) - значение настройки
- description (TEXT) - описание настройки
- updated_at (TIMESTAMP) - дата последнего обновления

## 8.3 Индексы

Для обеспечения производительности должны быть созданы следующие индексы:

### 8.3.1 Индексы для таблицы "bookings"
- Индекс по booking_date и start_time для быстрого поиска записей в определенный день и время
- Индекс по telegram_user_id для быстрого поиска записей конкретного пользователя
- Индекс по booking_status для фильтрации активных/отмененных записей

### 8.3.2 Индексы для таблицы "schedules"
- Индекс по day_of_week для быстрого получения расписания по дням недели

### 8.3.3 Индексы для таблицы "specific_dates"
- Индекс по date для быстрого доступа к исключениям по конкретной дате

## 8.4 Связи между таблицами

- Таблица "bookings" связана с таблицей "users" по полю telegram_id
- Для проверки расписания в определенную дату будет объединяться информация из таблиц "schedules" и "specific_dates"

## 8.5 Требования к хранению данных

- Обеспечение целостности данных с использованием внешних ключей
- Использование транзакций для обеспечения согласованности при бронировании
- Резервное копирование базы данных
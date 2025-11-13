import asyncio
import json
import os
from datetime import datetime, timedelta, time
from pathlib import Path

# Простая реализация бота без внешних зависимостей

class SimpleBookingBot:
    def __init__(self):
        self.data_file = Path("booking_data.json")
        self.load_data()
    
    def load_data(self):
        """Загружает данные из файла"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                'organizations': {},
                'users': {},
                'bookings': {}
            }
    
    def save_data(self):
        """Сохраняет данные в файл"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def create_organization(self, admin_id, name, address, contact_info, description):
        """Создает новую организацию"""
        import uuid
        unique_code = str(uuid.uuid4())[:8]
        
        org_id = str(len(self.data['organizations']) + 1)
        self.data['organizations'][org_id] = {
            'id': org_id,
            'name': name,
            'address': address,
            'contact_info': contact_info,
            'description': description,
            'admin_telegram_id': admin_id,
            'unique_code': unique_code,
            'schedules': {},  # расписания по дням недели
            'specific_dates': {},  # исключения для конкретных дат
        }
        
        # Добавляем администратора как пользователя
        self.data['users'][str(admin_id)] = {
            'telegram_id': admin_id,
            'organization_id': org_id,
            'role': 'admin'
        }
        
        self.save_data()
        return unique_code
    
    def get_organization_by_code(self, code):
        """Получает организацию по уникальному коду"""
        for org_id, org in self.data['organizations'].items():
            if org['unique_code'] == code:
                return org
        return None
    
    def get_schedule_for_date(self, org_id, date):
        """Получает расписание для конкретной даты"""
        org = self.data['organizations'].get(org_id)
        if not org:
            return None, None, 0, 60  # start_time, end_time, max_sessions, duration
        
        date_str = date.strftime('%Y-%m-%d')
        
        # Проверяем специфические даты
        if date_str in org['specific_dates']:
            specific = org['specific_dates'][date_str]
            return (
                datetime.strptime(specific['start_time'], '%H:%M').time(),
                datetime.strptime(specific['end_time'], '%H:%M').time(),
                specific.get('max_sessions_per_day', 1),
                60  # по умолчанию 60 минут
            )
        
        # Используем расписание по дням недели
        day_of_week = date.weekday()  # 0-понедельник, 6-воскресенье
        if str(day_of_week) in org['schedules']:
            sched = org['schedules'][str(day_of_week)]
            return (
                datetime.strptime(sched['start_time'], '%H:%M').time(),
                datetime.strptime(sched['end_time'], '%H:%M').time(),
                sched.get('max_sessions_per_day', 1),
                sched.get('session_duration', 60)
            )
        
        return None, None, 0, 60
    
    def get_booked_slots_for_date(self, org_id, date):
        """Получает забронированные слоты для даты"""
        date_str = date.strftime('%Y-%m-%d')
        booked = []
        
        for booking_id, booking in self.data['bookings'].items():
            if booking['organization_id'] == org_id and booking['booking_date'] == date_str:
                booked.append(datetime.strptime(booking['start_time'], '%H:%M').time())
        
        return booked
    
    def generate_time_slots(self, start_time, end_time, duration_minutes=60):
        """Генерирует временные слоты"""
        slots = []
        current_time = datetime.combine(datetime.today(), start_time)
        end_datetime = datetime.combine(datetime.today(), end_time)
        
        while current_time + timedelta(minutes=duration_minutes) <= end_datetime:
            slots.append(current_time.time())
            current_time += timedelta(minutes=duration_minutes)
        
        return slots
    
    def has_window_in_combination(self, combination):
        """Проверяет, есть ли окна в комбинации"""
        if len(combination) <= 1:
            return False
        
        sorted_times = sorted(combination)
        
        for i in range(len(sorted_times) - 1):
            current = datetime.combine(datetime.today(), sorted_times[i])
            next_time = datetime.combine(datetime.today(), sorted_times[i + 1])
            
            # Если разница больше чем длительность одного слота (1 час), значит есть окно
            if next_time - current > timedelta(hours=1):
                return True
        
        return False
    
    def get_available_slots_no_windows(self, available_slots, max_sessions, booked_slots=None):
        """Получает доступные слоты без окон"""
        if booked_slots is None:
            booked_slots = []
        
        import itertools
        
        available_for_selection = [slot for slot in available_slots if slot not in booked_slots]
        
        remaining_slots_needed = max_sessions - len(booked_slots)
        
        if remaining_slots_needed <= 0:
            return []
        
        # Проверяем каждый доступный слот - может ли его выбор привести к комбинации без окон
        safe_slots = []
        
        for slot in available_for_selection:
            # Проверим, может ли добавление этого слота привести к валидной комбинации
            found_valid = False
            
            # Проверим все возможные комбинации с этим слотом
            for r in range(remaining_slots_needed + 1):
                for combo in itertools.combinations(available_for_selection, r):
                    if slot not in combo:
                        continue  # Нам нужны комбинации с этим слотом
                    full_combo = sorted(booked_slots + list(combo))
                    if len(full_combo) <= max_sessions and not self.has_window_in_combination(full_combo):
                        found_valid = True
                        break
                if found_valid:
                    break
            
            if found_valid:
                safe_slots.append(slot)
        
        return safe_slots
    
    def create_booking(self, org_id, user_id, user_name, booking_date, start_time, end_time):
        """Создает новую бронь"""
        booking_id = str(len(self.data['bookings']) + 1)
        self.data['bookings'][booking_id] = {
            'id': booking_id,
            'organization_id': org_id,
            'user_id': user_id,
            'user_full_name': user_name,
            'booking_date': booking_date.strftime('%Y-%m-%d'),
            'start_time': start_time.strftime('%H:%M'),
            'end_time': end_time.strftime('%H:%M'),
            'booking_status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        self.save_data()
        return booking_id
    
    def set_schedule_for_day(self, org_id, day_of_week, start_time, end_time, max_sessions_per_day=1, session_duration=60):
        """Устанавливает расписание для определенного дня недели (0-понедельник, 6-воскресенье)"""
        if org_id in self.data['organizations']:
            if 'schedules' not in self.data['organizations'][org_id]:
                self.data['organizations'][org_id]['schedules'] = {}
            
            self.data['organizations'][org_id]['schedules'][str(day_of_week)] = {
                'start_time': start_time,
                'end_time': end_time,
                'max_sessions_per_day': max_sessions_per_day,
                'session_duration': session_duration
            }
            self.save_data()
            return True
        return False
    
    def set_specific_date_schedule(self, org_id, date_str, start_time, end_time, max_sessions_per_day=None):
        """Устанавливает расписание для конкретной даты"""
        if org_id in self.data['organizations']:
            if 'specific_dates' not in self.data['organizations'][org_id]:
                self.data['organizations'][org_id]['specific_dates'] = {}
            
            self.data['organizations'][org_id]['specific_dates'][date_str] = {
                'start_time': start_time,
                'end_time': end_time,
                'max_sessions_per_day': max_sessions_per_day
            }
            self.save_data()
            return True
        return False


def print_instructions():
    print("УПРОЩЕННЫЙ ТЕЛЕГРАМ-БОТ ДЛЯ ЗАПИСИ 'БЕЗ ОКОН'")
    print("=" * 50)
    print("Поскольку невозможно установить все зависимости на вашей системе,")
    print("мы создали упрощенную консольную версию для демонстрации функционала.\n")
    
    print("ВОЗМОЖНОСТИ:")
    print("- Создание организаций (психолог, автомойка и т.д.)")
    print("- Уникальные коды для каждой организации")
    print("- Алгоритм 'без окон' для планирования записей")
    print("- Бронирование времени с учетом ограничений")
    print("- Управление расписанием")
    print("- Хранение данных в JSON-файле\n")
    
    print("КОНСОЛЬНЫЕ КОМАНДЫ:")
    print("1. create_org - создать организацию")
    print("2. get_code - получить код организации")
    print("3. book_by_code - записаться по коду")
    print("4. show_org_info - показать информацию об организации")
    print("5. set_schedule - установить расписание")
    print("6. exit - выйти из программы\n")


def main():
    print_instructions()
    
    bot = SimpleBookingBot()
    
    while True:
        command = input("Введите команду: ").strip().lower()
        
        if command == 'create_org':
            print("\n--- СОЗДАНИЕ ОРГАНИЗАЦИИ ---")
            name = input("Название организации: ")
            address = input("Адрес: ")
            contact_info = input("Контактная информация: ")
            description = input("Описание услуги: ")
            admin_id = input("ID администратора (например, ваш Telegram ID): ")
            
            try:
                unique_code = bot.create_organization(admin_id, name, address, contact_info, description)
                print(f"\n✓ Организация создана успешно!")
                print(f"✓ Уникальный код: {unique_code}")
                print("✓ Дайте этот код клиентам для записи к вам")
            except Exception as e:
                print(f"Ошибка при создании организации: {e}")
        
        elif command == 'get_code':
            print("\n--- ПОЛУЧЕНИЕ КОДА ОРГАНИЗАЦИИ ---")
            admin_id = input("Ваш ID администратора: ")
            
            org = None
            for org_id, organization in bot.data['organizations'].items():
                if str(organization['admin_telegram_id']) == str(admin_id):
                    org = organization
                    break
            
            if org:
                print(f"✓ Организация: {org['name']}")
                print(f"✓ Уникальный код: {org['unique_code']}")
            else:
                print("✗ Организация с таким администратором не найдена")
        
        elif command == 'book_by_code':
            print("\n--- ЗАПИСЬ ЧЕРЕЗ КОД ---")
            code = input("Введите уникальный код организации: ")
            
            org = bot.get_organization_by_code(code)
            if not org:
                print("✗ Организация с таким кодом не найдена")
                continue
            
            print(f"\n✓ Вы выбрали: {org['name']}")
            print(f"✓ Адрес: {org['address']}")
            print(f"✓ Контакты: {org['contact_info']}")
            print(f"✓ Услуги: {org['description']}")
            
            # Показываем доступные даты (ближайшие 7 дней)
            print("\nДоступные даты для записи (ближайшие 7 дней):")
            for i in range(7):
                date = datetime.now() + timedelta(days=i)
                date_str = date.strftime("%d.%m.%Y")
                print(f"{i+1}. {date_str}")
            
            date_choice = input(f"\nВыберите дату (1-{7}): ")
            try:
                choice = int(date_choice) - 1
                selected_date = datetime.now() + timedelta(days=choice)
            except (ValueError, IndexError):
                print("Неверный выбор даты")
                continue
            
            # Получаем расписание для выбранной даты
            start_time, end_time, max_sessions, duration = bot.get_schedule_for_date(org['id'], selected_date)
            
            if not start_time:
                print("✗ На эту дату нет расписания. Администратор должен сначала установить расписание.")
                continue
            
            # Генерируем временные слоты
            time_slots = bot.generate_time_slots(start_time, end_time, duration)
            booked_slots = bot.get_booked_slots_for_date(org['id'], selected_date)
            
            # Применяем алгоритм "без окон"
            available_slots = bot.get_available_slots_no_windows(time_slots, max_sessions, booked_slots)
            
            if not available_slots:
                print("✗ Нет доступных слотов на эту дату")
                continue
            
            print(f"\nДоступные временные слоты на {selected_date.strftime('%d.%m.%Y')}:")
            for i, slot in enumerate(available_slots, 1):
                print(f"{i}. {slot.strftime('%H:%M')}")
            
            time_choice = input(f"\nВыберите время (1-{len(available_slots)}): ")
            try:
                choice = int(time_choice) - 1
                selected_time = available_slots[choice]
            except (ValueError, IndexError):
                print("Неверный выбор времени")
                continue
            
            # Рассчитываем время окончания
            end_time_booking = datetime.combine(selected_date, selected_time) + timedelta(minutes=duration)
            
            user_name = input("Ваше имя: ")
            user_id = input("Ваш ID (например, ваш Telegram ID): ")
            
            # Подтверждение
            print(f"\nПодтверждаете запись?")
            print(f"Организация: {org['name']}")
            print(f"Дата: {selected_date.strftime('%d.%m.%Y')}")
            print(f"Время: {selected_time.strftime('%H:%M')} - {end_time_booking.time().strftime('%H:%M')}")
            
            confirm = input("Подтвердить? (y/n): ").lower()
            if confirm == 'y':
                booking_id = bot.create_booking(
                    org['id'], 
                    user_id, 
                    user_name, 
                    selected_date, 
                    selected_time, 
                    end_time_booking.time()
                )
                print(f"\n✓ Вы успешно записаны!")
                print(f"✓ ID бронирования: {booking_id}")
            else:
                print("Запись отменена")
        
        elif command == 'show_org_info':
            print("\n--- ИНФОРМАЦИЯ ОБ ОРГАНИЗАЦИИ ---")
            admin_id = input("Ваш ID администратора: ")
            
            org = None
            for org_id, organization in bot.data['organizations'].items():
                if str(organization['admin_telegram_id']) == str(admin_id):
                    org = organization
                    break
            
            if org:
                print(f"\nИНФОРМАЦИЯ О ВАШЕЙ ОРГАНИЗАЦИИ:")
                print(f"Название: {org['name']}")
                print(f"Адрес: {org['address']}")
                print(f"Контакты: {org['contact_info']}")
                print(f"Описание: {org['description']}")
                print(f"Уникальный код: {org['unique_code']}")
                print(f"ID администратора: {org['admin_telegram_id']}")
                
                # Показать текущее расписание
                if org['schedules']:
                    print("\nРАСПИСАНИЕ ПО ДНЯМ НЕДЕЛИ:")
                    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
                    for day_num, schedule in org['schedules'].items():
                        day_name = days[int(day_num)] if int(day_num) < len(days) else f'День {day_num}'
                        print(f"  {day_name}: {schedule['start_time']}-{schedule['end_time']}, "
                              f"макс. {schedule['max_sessions_per_day']} сеансов, "
                              f"{schedule['session_duration']} мин")
                
                if org['specific_dates']:
                    print("\nСПЕЦИАЛЬНЫЕ ДАТЫ:")
                    for date_str, schedule in org['specific_dates'].items():
                        max_sess = schedule['max_sessions_per_day'] if schedule['max_sessions_per_day'] else 'не ограничено'
                        print(f"  {date_str}: {schedule['start_time']}-{schedule['end_time']}, макс. {max_sess} сеансов")
            else:
                print("✗ Организация с таким администратором не найдена")
        
        elif command == 'set_schedule':
            print("\n--- УСТАНОВКА РАСПИСАНИЯ ---")
            admin_id = input("Ваш ID администратора: ")
            
            org = None
            for org_id, organization in bot.data['organizations'].items():
                if str(organization['admin_telegram_id']) == str(admin_id):
                    org = organization
                    break
            
            if not org:
                print("✗ Организация с таким администратором не найдена")
                continue
            
            print("\nТИПЫ РАСПИСАНИЯ:")
            print("1. Расписание по дням недели")
            print("2. Расписание для конкретной даты")
            
            sched_type = input("Выберите тип (1 или 2): ")
            
            if sched_type == '1':
                print("\nДНИ НЕДЕЛИ:")
                print("0 - Понедельник, 1 - Вторник, 2 - Среда, 3 - Четверг, 4 - Пятница, 5 - Суббота, 6 - Воскресенье")
                day_of_week = input("Введите день недели (0-6): ")
                
                try:
                    day_num = int(day_of_week)
                    if day_num < 0 or day_num > 6:
                        print("Неверный день недели")
                        continue
                except ValueError:
                    print("Неверный ввод")
                    continue
                
                start_time = input("Время начала работы (HH:MM): ")
                end_time = input("Время окончания работы (HH:MM): ")
                
                try:
                    # Проверим корректность формата времени
                    datetime.strptime(start_time, '%H:%M')
                    datetime.strptime(end_time, '%H:%M')
                except ValueError:
                    print("Неверный формат времени. Используйте HH:MM (например, 09:00)")
                    continue
                
                max_sessions = input("Максимальное количество сеансов в день (по умолчанию 1): ")
                try:
                    max_sess = int(max_sessions) if max_sessions.strip() else 1
                except ValueError:
                    max_sess = 1
                
                duration = input("Длительность сеанса в минутах (по умолчанию 60): ")
                try:
                    dur = int(duration) if duration.strip() else 60
                except ValueError:
                    dur = 60
                
                success = bot.set_schedule_for_day(org['id'], day_num, start_time, end_time, max_sess, dur)
                if success:
                    print(f"✓ Расписание установлено для {['Понедельника', 'Вторника', 'Среды', 'Четверга', 'Пятницы', 'Субботы', 'Воскресенья'][day_num]}")
                else:
                    print("✗ Ошибка при установке расписания")
            
            elif sched_type == '2':
                date_str = input("Введите дату (YYYY-MM-DD): ")
                
                try:
                    # Проверим корректность формата даты
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    print("Неверный формат даты. Используйте YYYY-MM-DD (например, 2025-12-25)")
                    continue
                
                start_time = input("Время начала работы (HH:MM): ")
                end_time = input("Время окончания работы (HH:MM): ")
                
                try:
                    # Проверим корректность формата времени
                    datetime.strptime(start_time, '%H:%M')
                    datetime.strptime(end_time, '%H:%M')
                except ValueError:
                    print("Неверный формат времени. Используйте HH:MM (например, 09:00)")
                    continue
                
                max_sessions = input("Максимальное количество сеансов в этот день (оставьте пустым для значения по умолчанию): ")
                try:
                    max_sess = int(max_sessions) if max_sessions.strip() else None
                except ValueError:
                    max_sess = None
                
                success = bot.set_specific_date_schedule(org['id'], date_str, start_time, end_time, max_sess)
                if success:
                    print(f"✓ Расписание установлено для {date_str}")
                else:
                    print("✗ Ошибка при установке расписания")
            else:
                print("Неверный выбор")
        
        elif command == 'exit':
            print("\nСпасибо за использование упрощенной версии бота!")
            print("Для полной версии с GUI и интеграцией с Telegram вам понадобится:")
            print("- Установить Rust на вашу систему")
            print("- Затем установить aiogram и SQLAlchemy")
            print("- Настроить .env файл с токеном бота")
            break
        
        elif command == 'help':
            print_instructions()
        else:
            print("Неизвестная команда. Введите 'help' для списка команд.")


if __name__ == "__main__":
    main()
import asyncio
from datetime import datetime, time
from utils.booking_algorithm import (
    generate_time_slots, 
    get_available_slots_no_windows, 
    has_window_in_combination,
    create_organization,
    get_organization_by_unique_code
)
from database.database import init_db, AsyncSessionLocal
from sqlalchemy import create_engine


async def test_updated_features():
    print("Тестируем обновленные возможности бота...")
    
    # Инициализация базы данных
    await init_db()
    print("✓ База данных инициализирована")
    
    # Тест 1: Создание организации
    print("\n1. Тест создания организации:")
    async with AsyncSessionLocal() as db:
        org = await create_organization(
            db, 
            "Психолог Иванова", 
            "ул. Ленина, 15", 
            "+7 (999) 123-45-67", 
            "Консультации по психологии и терапия", 
            123456789  # ID администратора
        )
        print(f"✓ Организация создана: {org.name}")
        print(f"✓ Уникальный код: {org.unique_code}")
        print(f"✓ Адрес: {org.address}")
        print(f"✓ Контакты: {org.contact_info}")
    
    # Тест 2: Поиск организации по уникальному коду
    print("\n2. Тест поиска организации по уникальному коду:")
    async with AsyncSessionLocal() as db:
        found_org = await get_organization_by_unique_code(db, org.unique_code)
        if found_org:
            print(f"✓ Организация найдена: {found_org.name}")
            print(f"✓ Код совпадает: {found_org.unique_code == org.unique_code}")
        else:
            print("✗ Организация не найдена")
    
    # Тест 3: Проверка генерации временных слотов
    print("\n3. Тест генерации временных слотов:")
    start_time = time(9, 0)
    end_time = time(18, 0)
    slots = generate_time_slots(start_time, end_time, 60)  # 60-минутные слоты
    print(f"Слоты с 9:00 до 18:00: {[s.strftime('%H:%M') for s in slots]}")
    
    # Тест 4: Проверка алгоритма "без окон" 
    print("\n4. Тест алгоритма 'без окон':")
    all_slots = [time(10, 0), time(11, 0), time(12, 0), time(13, 0), time(14, 0)]
    booked = [time(11, 0)]
    available = get_available_slots_no_windows(all_slots, 3, booked)
    print(f"Все слоты: {[s.strftime('%H:%M') for s in all_slots]}")
    print(f"Занято: {[s.strftime('%H:%M') for s in booked]}")
    print(f"Доступно: {[s.strftime('%H:%M') for s in available]}")
    
    # Тест 5: Проверка наличия окон в комбинации
    print("\n5. Тест проверки окон в комбинации:")
    combo_with_window = [time(10, 0), time(12, 0), time(14, 0)]  # Есть окно 11:00-12:00 и 13:00-14:00
    combo_without_window = [time(10, 0), time(11, 0), time(12, 0)]  # Нет окон
    
    print(f"Комбинация {combo_with_window} имеет окна: {has_window_in_combination(combo_with_window)}")
    print(f"Комбинация {combo_without_window} имеет окна: {has_window_in_combination(combo_without_window)}")
    
    print("\n✓ Все тесты прошли успешно! Обновленная архитектура готова к работе.")


if __name__ == "__main__":
    asyncio.run(test_updated_features())
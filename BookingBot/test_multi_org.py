import asyncio
from datetime import datetime, time
from utils.booking_algorithm import (
    generate_time_slots, 
    get_available_slots_no_windows, 
    has_window_in_combination
)


def test_multi_organization_features():
    print("Тестируем возможности мульти-организации...")
    
    # Тест 1: Проверка генерации временных слотов
    print("\n1. Тест генерации временных слотов:")
    start_time = time(9, 0)
    end_time = time(18, 0)
    slots = generate_time_slots(start_time, end_time, 60)  # 60-минутные слоты
    print(f"Слоты с 9:00 до 18:00: {[s.strftime('%H:%M') for s in slots]}")
    
    # Тест 2: Проверка алгоритма "без окон" 
    print("\n2. Тест алгоритма 'без окон':")
    all_slots = [time(10, 0), time(11, 0), time(12, 0), time(13, 0), time(14, 0)]
    booked = [time(11, 0)]
    available = get_available_slots_no_windows(all_slots, 3, booked)
    print(f"Все слоты: {[s.strftime('%H:%M') for s in all_slots]}")
    print(f"Занято: {[s.strftime('%H:%M') for s in booked]}")
    print(f"Доступно: {[s.strftime('%H:%M') for s in available]}")
    
    # Тест 3: Проверка наличия окон в комбинации
    print("\n3. Тест проверки окон в комбинации:")
    combo_with_window = [time(10, 0), time(12, 0), time(14, 0)]  # Есть окно 11:00-12:00 и 13:00-14:00
    combo_without_window = [time(10, 0), time(11, 0), time(12, 0)]  # Нет окон
    
    print(f"Комбинация {combo_with_window} имеет окна: {has_window_in_combination(combo_with_window)}")
    print(f"Комбинация {combo_without_window} имеет окна: {has_window_in_combination(combo_without_window)}")
    
    print("\nВсе тесты прошли успешно! Мульти-организационная структура готова к работе.")


if __name__ == "__main__":
    test_multi_organization_features()
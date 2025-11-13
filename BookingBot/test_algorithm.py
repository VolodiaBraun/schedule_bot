import asyncio
from datetime import time
from utils.booking_algorithm import get_available_slots_no_windows, generate_time_slots


def test_booking_algorithm():
    print("Тестируем алгоритм 'без окон'...")
    
    # Тест 1: Базовый сценарий
    print("\nТест 1: Начальное состояние (никто не записан)")
    start_time = time(16, 0)
    end_time = time(20, 0)
    time_slots = generate_time_slots(start_time, end_time, 60)  # 60-минутные слоты
    print(f"Все временные слоты: {[t.strftime('%H:%M') for t in time_slots]}")
    
    max_sessions = 3
    booked_slots = []
    available = get_available_slots_no_windows(time_slots, max_sessions, booked_slots)
    print(f"Доступные слоты: {[t.strftime('%H:%M') for t in available]}")
    print(f"Ожидаем: все слоты (16:00, 17:00, 18:00, 19:00) - {len(available)} шт.")
    
    # Тест 2: После записи первого клиента на 17:00
    print("\nТест 2: После записи на 17:00")
    booked_slots = [time(17, 0)]
    available = get_available_slots_no_windows(time_slots, max_sessions, booked_slots)
    print(f"Занятые слоты: {[t.strftime('%H:%M') for t in booked_slots]}")
    print(f"Доступные слоты: {[t.strftime('%H:%M') for t in available]}")
    print("По логике 'без окон', должны быть доступны 16:00 и 18:00, но не 19:00 (т.к. 19:00 + 17:00 создают окно 18:00)")
    
    # Тест 3: После записи на 17:00 и 18:00
    print("\nТест 3: После записи на 17:00 и 18:00")
    booked_slots = [time(17, 0), time(18, 0)]
    available = get_available_slots_no_windows(time_slots, max_sessions, booked_slots)
    print(f"Занятые слоты: {[t.strftime('%H:%M') for t in booked_slots]}")
    print(f"Доступные слоты: {[t.strftime('%H:%M') for t in available]}")
    print("Должны быть доступны 16:00 и 19:00")
    
    # Тест 4: После записи на 16:00, 17:00, 18:00
    print("\nТест 4: После записи на 16:00, 17:00, 18:00 (достигнут лимит)")
    booked_slots = [time(16, 0), time(17, 0), time(18, 0)]
    available = get_available_slots_no_windows(time_slots, max_sessions, booked_slots)
    print(f"Занятые слоты: {[t.strftime('%H:%M') for t in booked_slots]}")
    print(f"Доступные слоты: {[t.strftime('%H:%M') for t in available]}")
    print("Доступных слотов быть не должно")


if __name__ == "__main__":
    test_booking_algorithm()
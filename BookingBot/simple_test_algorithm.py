from datetime import datetime, time, timedelta
from typing import List, Tuple


def generate_time_slots(start_time: time, end_time: time, duration_minutes: int = 60) -> List[time]:
    """
    Генерирует список временных слотов между start_time и end_time с заданной длительностью
    """
    slots = []
    current_time = datetime.combine(datetime.today(), start_time)
    end_datetime = datetime.combine(datetime.today(), end_time)
    
    while current_time + timedelta(minutes=duration_minutes) <= end_datetime:
        slots.append(current_time.time())
        current_time += timedelta(minutes=duration_minutes)
    
    return slots


def has_window_in_combination(combination: List[time]) -> bool:
    """
    Проверяет, есть ли "окно" в комбинации слотов
    Окно - это пропущенный слот между первым и последним в комбинации
    """
    if len(combination) <= 1:
        return False
    
    # Преобразуем в список с интервалами 60 минут
    times_in_order = sorted(combination)
    
    # Проверяем, есть ли пропущенные 60-минутные интервалы между слотами
    for i in range(len(times_in_order) - 1):
        current_time = datetime.combine(datetime.today(), times_in_order[i])
        next_time = datetime.combine(datetime.today(), times_in_order[i + 1])
        
        # Если разница больше чем длительность одного слота, значит есть "окно"
        if next_time - current_time > timedelta(minutes=60):
            return True
    
    return False


def get_available_slots_no_windows(available_slots: List[time], max_sessions: int, 
                                 booked_slots: List[time] = None) -> List[time]:
    """
    Возвращает список слотов, которые можно безопасно выбрать без риска создания "окна"
    """
    if booked_slots is None:
        booked_slots = []
    
    if len(booked_slots) >= max_sessions:
        return []
    
    import itertools
    
    available_for_selection = [slot for slot in available_slots if slot not in booked_slots]
    
    remaining_slots_needed = max_sessions - len(booked_slots)
    
    if remaining_slots_needed <= 0:
        return []
    
    # Проверяем каждый доступный слот - может ли его выбор привести к комбинации без окон
    safe_slots = []
    
    for slot in available_for_selection:
        # Проверяем все возможные комбинации, включающие этот слот
        # с оставшимися слотами
        found_valid_combination = False
        
        # Добавляем текущий слот к забронированным и проверяем комбинации
        temp_booked_with_slot = sorted(booked_slots + [slot])
        
        # Если в текущем наборе уже есть окна, пропускаем этот слот
        if has_window_in_combination(temp_booked_with_slot):
            continue
        
        # Проверяем, можно ли дополнить этот набор до допустимого количества сеансов
        remaining_available = [ts for ts in available_for_selection if ts != slot]
        
        # Проверяем все возможные комбинации оставшихся слотов для дополнения
        for r in range(remaining_slots_needed):
            for combo in itertools.combinations(remaining_available, r):
                full_combo = sorted(temp_booked_with_slot + list(combo))
                
                # Убедимся, что размер комбинации не превышает лимит
                if len(full_combo) <= max_sessions and not has_window_in_combination(full_combo):
                    found_valid_combination = True
                    break
            
            if found_valid_combination:
                break
        
        if found_valid_combination or len(temp_booked_with_slot) == max_sessions:
            # Если есть хотя бы одна валидная комбинация или этот слот заполняет лимит
            safe_slots.append(slot)
    
    return safe_slots


def test_booking_algorithm():
    print("Тестируем упрощенный алгоритм 'без окон'...")
    
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
    print("По логике 'без окон', должны быть доступны 16:00 и 18:00, но не 19:00")
    print("(т.к. выбор 19:00 может привести к комбинации [16:00, 17:00, 19:00] с окном 18:00)")
    
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
from datetime import datetime, time, timedelta
from typing import List, Tuple
from database.models import Booking, Schedule, SpecificDate, Organization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


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


def get_valid_combinations(available_slots: List[time], max_sessions: int, 
                          booked_slots: List[time] = None) -> List[List[time]]:
    """
    Возвращает все допустимые комбинации слотов без "окон"
    """
    if booked_slots is None:
        booked_slots = []
    
    import itertools
    
    valid_combinations = []
    
    # Сначала добавим уже забронированные слоты ко всем комбинациям
    available_for_selection = [slot for slot in available_slots if slot not in booked_slots]
    
    # Генерация всех возможных комбинаций
    remaining_slots_needed = max_sessions - len(booked_slots)
    
    if remaining_slots_needed <= 0:
        return [booked_slots] if booked_slots else [[]]
    
    for r in range(1, remaining_slots_needed + 1):
        for combo in itertools.combinations(available_for_selection, r):
            full_combo = sorted(list(booked_slots + list(combo)))
            if not has_window_in_combination(full_combo):
                valid_combinations.append(full_combo)
    
    return valid_combinations


def get_available_slots_no_windows(available_slots: List[time], max_sessions: int, 
                                 booked_slots: List[time] = None) -> List[time]:
    """
    Возвращает список слотов, которые можно безопасно выбрать без риска создания "окна"
    """
    if booked_slots is None:
        booked_slots = []
    
    if len(booked_slots) >= max_sessions:
        return []
    
    available_for_selection = [slot for slot in available_slots if slot not in booked_slots]
    
    remaining_slots_needed = max_sessions - len(booked_slots)
    
    if remaining_slots_needed <= 0:
        return []
    
    # Проверяем каждый доступный слот - может ли его выбор привести к комбинации без окон
    safe_slots = []
    
    for slot in available_for_selection:
        # Создаем временную комбинацию с этим слотом
        temp_booked = booked_slots + [slot]
        
        # Находим все возможные комбинации с этим слотом
        valid_combos = get_valid_combinations(available_slots, max_sessions, temp_booked)
        
        # Если существуют комбинации без окон, которые включают этот слот, добавляем его
        if valid_combos:
            # Проверяем, есть ли хотя бы одна комбинация, включающая этот слот
            slot_used = False
            for combo in valid_combos:
                if slot in combo:
                    slot_used = True
                    break
            if slot_used:
                safe_slots.append(slot)
    
    return safe_slots


async def get_booked_slots_for_date(db: AsyncSession, organization_id: int, date: datetime.date) -> List[time]:
    """
    Получает список забронированных слотов для конкретной организации и даты
    """
    result = await db.execute(
        select(Booking.start_time).where(
            Booking.organization_id == organization_id,
            Booking.booking_date == date,
            Booking.booking_status == "active"
        )
    )
    booked_times = result.scalars().all()
    return [bt for bt in booked_times]


async def get_schedule_for_date(db: AsyncSession, organization_id: int, date: datetime.date) -> Tuple[time, time, int, int]:
    """
    Получает расписание для конкретной организации и даты, учитывая специфические даты
    Возвращает: (start_time, end_time, max_sessions_per_day, session_duration)
    """
    # Сначала проверим, есть ли специфическое расписание для этой даты и организации
    specific_date = await db.execute(
        select(SpecificDate).where(
            SpecificDate.organization_id == organization_id,
            SpecificDate.date == date
        )
    )
    specific = specific_date.scalar_one_or_none()
    
    if specific:
        return (
            specific.start_time, 
            specific.end_time, 
            specific.max_sessions_per_day or 1,  # default to 1 if None
            60  # Предположим, что для специфических дат длительность по умолчанию 60 мин
        )
    
    # Если специфического расписания нет, используем по дням недели для организации
    day_of_week = date.weekday()  # 0 - понедельник, 6 - воскресенье
    
    schedule = await db.execute(
        select(Schedule).where(
            Schedule.organization_id == organization_id,
            Schedule.day_of_week == day_of_week,
            Schedule.is_active == True
        )
    )
    schedule_item = schedule.scalar_one_or_none()
    
    if schedule_item:
        return (
            schedule_item.start_time,
            schedule_item.end_time,
            schedule_item.max_sessions_per_day,
            schedule_item.session_duration
        )
    else:
        # Если нет расписания для этого дня и организации, возвращаем None
        return None, None, None, None


async def get_organization_by_unique_code(db: AsyncSession, unique_code: str) -> Organization:
    """
    Получает организацию по уникальному коду
    """
    result = await db.execute(
        select(Organization).where(Organization.unique_code == unique_code)
    )
    return result.scalar_one_or_none()


async def get_organization_by_admin_id(db: AsyncSession, admin_telegram_id: int) -> Organization:
    """
    Получает организацию по ID администратора
    """
    result = await db.execute(
        select(Organization).where(Organization.admin_telegram_id == admin_telegram_id)
    )
    return result.scalar_one_or_none()


async def create_organization(db: AsyncSession, name: str, address: str, contact_info: str, description: str, admin_telegram_id: int) -> Organization:
    """
    Создает новую организацию
    """
    org = Organization(
        name=name,
        address=address,
        contact_info=contact_info,
        description=description,
        admin_telegram_id=admin_telegram_id
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org
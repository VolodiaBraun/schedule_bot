from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Booking, User, Organization
from datetime import datetime, date, time
from typing import List, Optional
from sqlalchemy import select


async def register_user_if_not_exists(db: AsyncSession, telegram_id: int, full_name: str, organization_id: int, username: str = None, role: str = "client"):
    """Регистрирует пользователя в системе, если он еще не зарегистрирован"""
    existing_user = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = existing_user.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            organization_id=organization_id,
            role=role,
            created_at=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Обновляем время последнего взаимодействия
    user.last_interaction_at = datetime.utcnow()
    await db.commit()


async def create_booking(db: AsyncSession, organization_id: int, telegram_user_id: int, user_full_name: str, 
                        booking_date: date, start_time: time, end_time: time, service_type: str = None):
    """Создает новую бронь"""
    booking = Booking(
        organization_id=organization_id,
        telegram_user_id=telegram_user_id,
        user_full_name=user_full_name,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        service_type=service_type,
        booking_status="active",
        created_at=datetime.utcnow()
    )
    
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    
    return booking


async def get_user_bookings(db: AsyncSession, telegram_user_id: int, organization_id: int = None) -> List[Booking]:
    """Получает все бронирования пользователя"""
    query = select(Booking).where(
        Booking.telegram_user_id == telegram_user_id,
        Booking.booking_status == "active"
    ).order_by(Booking.booking_date, Booking.start_time)
    
    if organization_id:
        query = query.where(Booking.organization_id == organization_id)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_organization_bookings(db: AsyncSession, organization_id: int) -> List[Booking]:
    """Получает все бронирования для организации"""
    result = await db.execute(
        select(Booking).where(
            Booking.organization_id == organization_id,
            Booking.booking_status == "active"
        ).order_by(Booking.booking_date, Booking.start_time)
    )
    return result.scalars().all()


async def cancel_booking(db: AsyncSession, booking_id: int, telegram_user_id: int) -> bool:
    """Отменяет бронирование"""
    result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.telegram_user_id == telegram_user_id
        )
    )
    booking = result.scalar_one_or_none()
    
    if booking and booking.booking_status == "active":
        booking.booking_status = "cancelled"
        booking.cancelled_at = datetime.utcnow()
        await db.commit()
        return True
    
    return False


async def create_user(db: AsyncSession, telegram_id: int, full_name: str, username: str, organization_id: int, role: str = "client"):
    """Создает нового пользователя"""
    user = User(
        telegram_id=telegram_id,
        full_name=full_name,
        username=username,
        organization_id=organization_id,
        role=role,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> User:
    """Получает пользователя по его Telegram ID"""
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_organization_users(db: AsyncSession, organization_id: int) -> List[User]:
    """Получает всех пользователей организации"""
    result = await db.execute(
        select(User).where(User.organization_id == organization_id)
    )
    return result.scalars().all()


async def get_organization_by_id(db: AsyncSession, organization_id: int) -> Organization:
    """Получает организацию по ID"""
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    return result.scalar_one_or_none()
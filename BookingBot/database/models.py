from sqlalchemy import Column, Integer, String, DateTime, Time, Date, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base
import uuid


class Organization(Base):
    """Организация/бизнес (психолог, автомойка и т.д.)"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # название организации
    address = Column(String)  # адрес
    contact_info = Column(String)  # контактная информация
    description = Column(Text)  # описание услуги
    admin_telegram_id = Column(Integer, nullable=False)  # ID администратора (владельца)
    unique_code = Column(String, unique=True, default=lambda: str(uuid.uuid4())[:8])  # уникальный код для записи
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """Пользователь (администратор или клиент)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String)
    full_name = Column(String)
    organization_id = Column(Integer, ForeignKey("organizations.id"))  # к какой организации принадлежит
    role = Column(String, default="client")  # "admin", "client"
    created_at = Column(DateTime, default=datetime.utcnow)
    last_interaction_at = Column(DateTime, default=datetime.utcnow)


class Schedule(Base):
    """Расписание для организации"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)  # к какой организации относится
    day_of_week = Column(Integer)  # 0 - воскресенье, 1 - понедельник, ..., 6 - суббота
    start_time = Column(Time)
    end_time = Column(Time)
    max_sessions_per_day = Column(Integer, default=1)
    session_duration = Column(Integer, default=60)  # в минутах
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SpecificDate(Base):
    """Исключения для конкретных дат"""
    __tablename__ = "specific_dates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)  # к какой организации относится
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    max_sessions_per_day = Column(Integer)  # NULL означает использовать значение по умолчанию
    is_exception = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Booking(Base):
    """Бронирование"""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)  # к какой организации относится
    telegram_user_id = Column(Integer, index=True)
    user_full_name = Column(String)
    booking_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    booking_status = Column(String, default="active")  # active, cancelled, completed
    service_type = Column(String)  # тип услуги (для разных видов бизнеса)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)


class Setting(Base):
    """Настройки системы"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))  # может быть NULL для глобальных настроек
    setting_key = Column(String, nullable=False)
    setting_value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
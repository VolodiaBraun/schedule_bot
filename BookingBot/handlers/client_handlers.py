from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.main import get_main_keyboard, get_date_selection_keyboard, get_time_slot_keyboard
from utils.booking_algorithm import get_schedule_for_date, get_booked_slots_for_date, generate_time_slots, get_available_slots_no_windows, get_organization_by_unique_code
from database.database import SessionLocal
from database.models import Organization
from sqlalchemy import select
from datetime import datetime, time, timedelta
from utils.booking_service import register_user_if_not_exists, create_booking, get_user_by_telegram_id
from utils.states import BookingByCode
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Основное меню для нового пользователя"""
    await message.answer(
        "Привет! Я бот для записи к специалистам.\n"
        "Если вы клиент - используйте команду /book или /code для записи по уникальному коду.\n"
        "Если вы хотите создать свою организацию - используйте /setup.",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - начать взаимодействие с ботом\n"
        "/code - записаться по уникальному коду организации\n"
        "/book - записаться (если вы уже выбрали организацию)\n"
        "/my_bookings - посмотреть свои записи\n"
        "/setup - создать свою организацию\n"
        "/help - показать это сообщение"
    )

@router.message(Command("code"))
async def cmd_book_by_code(message: Message, state: FSMContext):
    """Начать запись по уникальному коду"""
    await message.answer("Отправьте уникальный код организации:")
    await state.set_state(BookingByCode.waiting_for_code)

@router.message(BookingByCode.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    """Обработать уникальный код"""
    with SessionLocal() as db:
        organization = get_organization_by_unique_code(db, message.text)
        if organization:
            await message.answer(f"Организация найдена: {organization.name}")
            await state.clear()
        else:
            await message.answer("Неверный код. Попытайтесь ещё.")

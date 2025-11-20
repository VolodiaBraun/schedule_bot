from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.main import get_admin_keyboard
from database.models import User
from database.database import SessionLocal
from sqlalchemy import select
from utils.booking_service import get_user_by_telegram_id, create_user
from utils.booking_algorithm import get_organization_by_admin_id, get_organization_by_unique_code, create_organization
from utils.states import OrganizationSetup
from aiogram.fsm.context import FSMContext

router = Router()

async def is_organization_admin(db, admin_telegram_id: int) -> bool:
    """Проверяет, является ли пользователь администратором какой-либо организации"""
    organization = await get_organization_by_admin_id(db, admin_telegram_id)
    return organization is not None

@router.message(Command("start"))
async def cmd_start(message: Message):
    # Создаем сессию базы данных
    with SessionLocal() as db:
        # Проверяем, есть ли организация у этого пользователя
        organization = await get_organization_by_admin_id(db, message.from_user.id)
        
        if not organization:
            # Если организация не существует, предлагаем создать
            await message.answer(
                "Добро пожаловать!\n"
                "Вы можете создать свою организацию (психолог, автомойка, и т.д.) и начать принимать записи от клиентов.\n"
                "Отправьте команду /setup для настройки своей организации."
            )
        else:
            await message.answer(
                f"Привет, администратор организации {organization.name}!\n"
                "Используй /admin для управления организацией.",
                reply_markup=get_admin_keyboard()
            )

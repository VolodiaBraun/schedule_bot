from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.main import get_admin_keyboard
from database.models import User
from database.database import AsyncSessionLocal
from sqlalchemy import select
from utils.booking_service import get_user_by_telegram_id, create_user
from utils.booking_algorithm import get_organization_by_admin_id, get_organization_by_unique_code, create_organization
from utils.states import OrganizationSetup
from aiogram.fsm.context import FSMContext

router = Router()


async def is_organization_admin(db: AsyncSession, admin_telegram_id: int) -> bool:
    """Проверяет, является ли пользователь администратором какой-либо организации"""
    organization = await get_organization_by_admin_id(db, admin_telegram_id)
    return organization is not None


@router.message(Command("start"))
async def cmd_start(message: Message):
    # Создаем сессию базы данных
    async with AsyncSessionLocal() as db:
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
            # Организация существует, проверяем, зарегистрирован ли пользователь
            user = await get_user_by_telegram_id(db, message.from_user.id)
            if not user:
                await message.answer(
                    f"Добро пожаловать в {organization.name}!\n"
                    "Для начала работы с ботом.",
                    # Здесь может быть клавиатура с кнопками для регистрации
                )
            else:
                await message.answer(
                    f"Добро пожаловать обратно в {organization.name}!",
                    # Здесь будет основное меню в зависимости от роли пользователя
                )


@router.message(Command("setup"))
async def cmd_setup(message: Message, state: FSMContext):
    # Проверяем, существует ли уже организация у этого пользователя
    async with AsyncSessionLocal() as db:
        organization = await get_organization_by_admin_id(db, message.from_user.id)
        
        if organization:
            await message.answer(
                f"У вас уже есть организация: '{organization.name}'.\n"
                f"Уникальный код для записи: {organization.unique_code}\n"
                f"Клиенты могут использовать этот код для записи к вам.\n\n"
                f"Если вы хотите настроить расписание, используйте команду /admin."
            )
            return
    
    # Начинаем процесс создания организации
    await state.set_state(OrganizationSetup.waiting_for_name)
    await message.answer(
        "Создание новой организации.\n"
        "Пожалуйста, введите название вашей организации (например, 'Психолог Иванова', 'Автомойка Сияние' и т.д.):"
    )


@router.message(OrganizationSetup.waiting_for_name)
async def process_org_name(message: Message, state: FSMContext):
    # Сохраняем название организации во временное состояние
    await state.update_data(org_name=message.text)
    await state.set_state(OrganizationSetup.waiting_for_address)
    await message.answer("Теперь введите адрес вашей организации (или '-' если не применимо):")


@router.message(OrganizationSetup.waiting_for_address)
async def process_org_address(message: Message, state: FSMContext):
    # Сохраняем адрес организации во временное состояние
    await state.update_data(org_address=message.text)
    await state.set_state(OrganizationSetup.waiting_for_contact_info)
    await message.answer("Теперь введите контактную информацию (телефон, email, соцсети и т.д.):")


@router.message(OrganizationSetup.waiting_for_contact_info)
async def process_org_contact_info(message: Message, state: FSMContext):
    # Сохраняем контактную информацию во временное состояние
    await state.update_data(org_contact_info=message.text)
    await state.set_state(OrganizationSetup.waiting_for_description)
    await message.answer("Теперь введите краткое описание вашей организации и предоставляемых услуг:")


@router.message(OrganizationSetup.waiting_for_description)
async def process_org_description(message: Message, state: FSMContext):
    # Завершаем процесс создания организации
    async with AsyncSessionLocal() as db:
        # Получаем все данные
        data = await state.get_data()
        
        org_name = data.get('org_name')
        org_address = data.get('org_address')
        org_contact_info = data.get('org_contact_info')
        org_description = message.text  # Это и есть описание
        admin_telegram_id = message.from_user.id  # Теперь используем ID пользователя как админа
        
        # Создаем новую организацию
        organization = await create_organization(
            db, 
            org_name, 
            org_address, 
            org_contact_info, 
            org_description, 
            admin_telegram_id
        )
        
        # Создаем администратора для этой организации
        admin_user = await create_user(
            db, 
            message.from_user.id, 
            message.from_user.full_name, 
            message.from_user.username or "", 
            organization.id, 
            "admin"
        )
        
        # Завершаем FSM
        await state.clear()
        
        await message.answer(
            f"Организация '{organization.name}' успешно создана!\n"
            f"Уникальный код для записи: {organization.unique_code}\n"
            f"Адрес: {organization.address}\n"
            f"Контакты: {organization.contact_info}\n"
            f"Описание: {organization.description}\n\n"
            f"Теперь вы являетесь администратором этой организации.\n"
            f"Клиенты могут использовать код {organization.unique_code} для записи к вам.\n"
            f"Используйте команду /admin для управления расписанием и записями."
        )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    async with AsyncSessionLocal() as db:
        # Проверяем, является ли пользователь администратором какой-либо организации
        organization = await get_organization_by_admin_id(db, message.from_user.id)
        if not organization:
            await message.answer(
                "Вы не являетесь администратором ни одной организации.\n"
                "Используйте команду /setup для создания своей организации."
            )
            return
        
        await message.answer(
            f"Вы вошли в административный режим для '{organization.name}'.\n"
            "Доступные команды:\n"
            "/schedule - управление расписанием\n"
            "/bookings - просмотр всех записей\n"
            "/settings - настройки бота\n"
            "/info - информация о вашей организации",
            reply_markup=get_admin_keyboard()
        )


@router.message(Command("info"))
async def cmd_info(message: Message):
    async with AsyncSessionLocal() as db:
        # Получаем организацию пользователя
        organization = await get_organization_by_admin_id(db, message.from_user.id)
        if not organization:
            await message.answer(
                "Вы не являетесь администратором ни одной организации.\n"
                "Используйте команду /setup для создания своей организации."
            )
            return
        
        await message.answer(
            f"Информация о вашей организации:\n"
            f"Название: {organization.name}\n"
            f"Адрес: {organization.address}\n"
            f"Контакты: {organization.contact_info}\n"
            f"Описание: {organization.description}\n"
            f"Уникальный код для записи: {organization.unique_code}\n"
            f"Дата создания: {organization.created_at.strftime('%d.%m.%Y %H:%M')}"
        )


@router.callback_query(lambda c: c.data == "manage_schedule")
async def cmd_manage_schedule(callback_query: CallbackQuery):
    async with AsyncSessionLocal() as db:
        organization = await get_organization_by_admin_id(db, callback_query.from_user.id)
        if not organization:
            await callback_query.answer("У вас нет прав администратора.", show_alert=True)
            return
            
        await callback_query.answer()
        await callback_query.message.edit_text(
            "Управление расписанием:\n"
            "1. Установить расписание по дням недели\n"
            "2. Установить исключения для конкретных дат\n"
            "3. Просмотреть текущее расписание"
        )


@router.callback_query(lambda c: c.data == "all_bookings")
async def cmd_all_bookings(callback_query: CallbackQuery):
    async with AsyncSessionLocal() as db:
        organization = await get_organization_by_admin_id(db, callback_query.from_user.id)
        if not organization:
            await callback_query.answer("У вас нет прав администратора.", show_alert=True)
            return
            
        await callback_query.answer()
        await callback_query.message.edit_text("Здесь будет отображаться список всех записей.")


@router.callback_query(lambda c: c.data == "settings")
async def cmd_settings(callback_query: CallbackQuery):
    async with AsyncSessionLocal() as db:
        organization = await get_organization_by_admin_id(db, callback_query.from_user.id)
        if not organization:
            await callback_query.answer("У вас нет прав администратора.", show_alert=True)
            return
            
        await callback_query.answer()
        await callback_query.message.edit_text("Настройки бота.")


@router.callback_query(lambda c: c.data == "back_to_main")
async def cmd_back_to_main(callback_query: CallbackQuery):
    await callback_query.answer()
    from keyboards.main import get_main_keyboard
    await callback_query.message.edit_text(
        "Привет! Я бот для записи к психологу. "
        "Вы можете записаться на сеанс или войти в административный режим, "
        "если вы являетесь администратором.",
        reply_markup=get_main_keyboard()
    )
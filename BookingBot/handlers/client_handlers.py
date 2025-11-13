from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.main import get_main_keyboard, get_date_selection_keyboard, get_time_slot_keyboard
from utils.booking_algorithm import get_schedule_for_date, get_booked_slots_for_date, generate_time_slots, get_available_slots_no_windows, get_organization_by_unique_code
from database.database import AsyncSessionLocal
from database.models import Organization
from sqlalchemy import select
from datetime import datetime, time, timedelta
from utils.booking_service import register_user_if_not_exists, create_booking, get_user_by_telegram_id
from utils.states import BookingByCode
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    # Просто показываем основное меню для нового пользователя
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
async def cmd_code(message: Message, state: FSMContext):
    await state.set_state(BookingByCode.waiting_for_org_code)
    await message.answer("Пожалуйста, введите уникальный код организации, к которой вы хотите записаться:")


@router.message(Command("book"))
@router.callback_query(lambda c: c.data == "book_appointment")
async def cmd_book(query, state: FSMContext):
    if isinstance(query, CallbackQuery):
        await query.answer()
        # Проверим, есть ли выбранная организация в состоянии
        data = await state.get_data()
        org_id = data.get('selected_org_id')
        
        if not org_id:
            await query.message.edit_text("Сначала выберите организацию. Используйте команду /code и введите уникальный код организации.")
            return
            
        await query.message.edit_text("Выберите дату для записи:", reply_markup=get_date_selection_keyboard())
    else:
        # Проверим, есть ли выбранная организация в состоянии
        data = await state.get_data()
        org_id = data.get('selected_org_id')
        
        if not org_id:
            await query.answer("Сначала выберите организацию. Используйте команду /code и введите уникальный код организации.")
            return
            
        await query.answer("Выберите дату для записи:", reply_markup=get_date_selection_keyboard())


@router.message(BookingByCode.waiting_for_org_code)
async def process_org_code(message: Message, state: FSMContext):
    code = message.text.strip()
    
    async with AsyncSessionLocal() as db:
        # Ищем организацию по уникальному коду
        organization = await get_organization_by_unique_code(db, code)
        
        if not organization:
            await message.answer("Организация с таким кодом не найдена. Пожалуйста, проверьте код и попробуйте снова.")
            await state.clear()
            return
        
        # Сохраняем выбранную организацию во временное состояние
        await state.update_data(selected_org_id=organization.id)
        
        await message.answer(
            f"Вы выбрали организацию: {organization.name}\n"
            f"Адрес: {organization.address}\n"
            f"Контакты: {organization.contact_info}\n"
            f"Услуги: {organization.description}\n\n"
            f"Теперь вы можете записаться, используя команду /book"
        )
        await state.clear()


@router.message(Command("my_bookings"))
@router.callback_query(lambda c: c.data == "my_bookings")
async def cmd_my_bookings(query):
    if isinstance(query, CallbackQuery):
        await query.answer()
        # Получаем ID пользователя
        user_id = query.from_user.id
        user_name = query.from_user.full_name
        
        async with AsyncSessionLocal() as db:
            # Получаем сохраненную организацию из состояния или используем другую логику
            # В реальном приложении нужно будет хранить историю записей пользователя
            # и отображать все его записи из всех организаций
            user = await get_user_by_telegram_id(db, user_id)
            
            if user:
                # Если пользователь уже зарегистрирован в какой-то организации
                # можно показать его записи в этой организации
                await query.message.edit_text("Ваши записи будут отображены здесь.")
            else:
                # Если пользователь не зарегистрирован нигде, показываем все его записи
                await query.message.edit_text("Ваши записи будут отображены здесь.")
    else:
        await query.answer("У вас пока нет записей.")


@router.callback_query(lambda c: c.data.startswith("select_date_"))
async def process_selected_date(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    # Извлекаем дату из callback_data
    selected_date_str = callback_query.data.replace("select_date_", "")
    
    # Преобразуем строку даты в объект даты
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    
    # Получаем сессию базы данных
    async with AsyncSessionLocal() as db:
        # Получаем выбранную организацию из состояния
        data = await state.get_data()
        org_id = data.get('selected_org_id')
        
        if not org_id:
            await callback_query.message.edit_text("Ошибка: организация не выбрана. Используйте команду /code для выбора организации.")
            return
        
        # Получаем организацию из базы данных по ID
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        organization = result.scalar_one_or_none()
        
        if not organization:
            await callback_query.message.edit_text("Ошибка: организация не найдена.")
            return
        
        # Получаем расписание для выбранной даты и организации
        start_time, end_time, max_sessions, session_duration = await get_schedule_for_date(db, organization.id, selected_date)
        
        if not start_time:
            await callback_query.message.edit_text(f"На {selected_date_str} нет расписания для записи в {organization.name}.")
            return
        
        # Генерируем временные слоты
        time_slots = generate_time_slots(start_time, end_time, session_duration)
        
        # Получаем забронированные слоты для этой даты и организации
        booked_slots = await get_booked_slots_for_date(db, organization.id, selected_date)
        
        # Применяем алгоритм "без окон", чтобы получить доступные слоты
        available_slots = get_available_slots_no_windows(time_slots, max_sessions, booked_slots)
        
        if not available_slots:
            await callback_query.message.edit_text(f"На {selected_date_str} нет доступных слотов для записи в {organization.name}.")
            return
        
        # Отправляем доступные временные слоты для выбора
        await callback_query.message.edit_text(
            f"Доступные слоты на {selected_date_str} в {organization.name}:\nВыберите время для записи.",
            reply_markup=get_time_slot_keyboard(available_slots)
        )


@router.callback_query(lambda c: c.data.startswith("select_time_"))
async def process_selected_time(callback_query: CallbackQuery):
    await callback_query.answer()
    
    # Извлекаем время из callback_data
    selected_time_str = callback_query.data.replace("select_time_", "")
    
    # Сохраняем выбранное время в состоянии (временно используем оперативную память)
    # В реальном приложении нужно использовать FSM (Finite State Machine) из aiogram
    state_data = getattr(callback_query.message, 'state_data', {})
    state_data['selected_time'] = selected_time_str
    
    # Извлекаем дату из последнего сообщения пользователя (упрощенная логика)
    # В реальной реализации нужно использовать FSM для сохранения контекста
    message_text = callback_query.message.text
    import re
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', message_text)
    
    if not date_match:
        await callback_query.message.edit_text("Ошибка: не удалось определить дату. Пожалуйста, начните сначала.")
        return
    
    selected_date_str = date_match.group(1)
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    selected_time = datetime.strptime(selected_time_str, "%H:%M").time()
    
    # Рассчитываем время окончания (предполагаем, что сеанс длится 1 час)
    end_time = datetime.combine(selected_date, selected_time) + timedelta(hours=1)
    end_time = end_time.time()
    
    # Подтверждение бронирования
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="✅ Подтвердить", 
        callback_data=f"confirm_booking_{selected_date_str}_{selected_time_str}"
    ))
    keyboard.add(InlineKeyboardButton(
        text="❌ Отменить", 
        callback_data="cancel_booking"
    ))
    
    await callback_query.message.edit_text(
        f"Подтверждаете запись?\n"
        f"Дата: {selected_date_str}\n"
        f"Время: {selected_time_str} - {end_time.strftime('%H:%M')}",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(lambda c: c.data.startswith("confirm_booking_"))
async def confirm_booking(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    # Извлекаем дату и время из callback_data
    parts = callback_query.data.split("_")
    if len(parts) < 4:
        await callback_query.message.edit_text("Ошибка при подтверждении записи.")
        return
    
    date_str = f"{parts[2]}-{parts[3]}-{parts[4]}"
    time_str = parts[5]
    
    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    selected_time = datetime.strptime(time_str, "%H:%M").time()
    
    # Рассчитываем время окончания
    end_time = datetime.combine(selected_date, selected_time) + timedelta(hours=1)
    end_time = end_time.time()
    
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.full_name
    
    async with AsyncSessionLocal() as db:
        # Получаем выбранную организацию из состояния
        data = await state.get_data()
        org_id = data.get('selected_org_id')
        
        if not org_id:
            await callback_query.message.edit_text("Ошибка: организация не выбрана. Используйте команду /code для выбора организации.")
            return
        
        # Получаем организацию из базы данных
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        organization = result.scalar_one_or_none()
        
        if not organization:
            await callback_query.message.edit_text("Ошибка: организация не найдена.")
            return
        
        # Получаем или создаем пользователя
        user = await get_user_by_telegram_id(db, user_id)
        if not user:
            # Регистрируем пользователя в этой организации
            await register_user_if_not_exists(db, user_id, user_name, organization.id, callback_query.from_user.username)
        else:
            # Проверяем, что пользователь принадлежит этой организации
            if user.organization_id != organization.id:
                await register_user_if_not_exists(db, user_id, user_name, organization.id, callback_query.from_user.username)
        
        # Создаем бронирование
        booking = await create_booking(
            db, 
            organization.id, 
            user_id, 
            user_name, 
            selected_date, 
            selected_time, 
            end_time
        )
        
        if booking:
            await callback_query.message.edit_text(
                f"Вы успешно записаны в {organization.name}!\n"
                f"Дата: {date_str}\n"
                f"Время: {time_str} - {end_time.strftime('%H:%M')}\n"
                f"ID бронирования: {booking.id}"
            )
        else:
            await callback_query.message.edit_text("Ошибка при создании записи. Пожалуйста, попробуйте снова.")


@router.callback_query(lambda c: c.data == "cancel_booking")
async def cancel_booking(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(
        "Бронирование отменено.",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(lambda c: c.data == "admin_panel")
async def cmd_admin_panel(callback_query: CallbackQuery):
    await callback_query.answer()
    from keyboards.main import get_admin_keyboard
    await callback_query.message.edit_text("Административная панель", reply_markup=get_admin_keyboard())
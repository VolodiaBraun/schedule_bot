from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta


def get_main_keyboard():
    """Основная клавиатура для клиентов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📅 Записаться", callback_data="book_appointment"))
    keyboard.add(InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings"))
    keyboard.add(InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel"))
    return keyboard.adjust(1).as_markup()


def get_admin_keyboard():
    """Клавиатура для администратора"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📊 Управление расписанием", callback_data="manage_schedule"))
    keyboard.add(InlineKeyboardButton(text="📋 Все записи", callback_data="all_bookings"))
    keyboard.add(InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"))
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return keyboard.adjust(1).as_markup()


def get_date_selection_keyboard():
    """Клавиатура для выбора даты"""
    keyboard = InlineKeyboardBuilder()
    
    # Показываем ближайшие 7 дней
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y (%A)")
        keyboard.add(InlineKeyboardButton(
            text=date_str, 
            callback_data=f"select_date_{date.strftime('%Y-%m-%d')}"
        ))
    
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return keyboard.adjust(1).as_markup()


def get_time_slot_keyboard(time_slots):
    """Клавиатура для выбора временного слота"""
    keyboard = InlineKeyboardBuilder()
    
    for time_slot in time_slots:
        time_str = time_slot.strftime("%H:%M")
        keyboard.add(InlineKeyboardButton(
            text=time_str, 
            callback_data=f"select_time_{time_str}"
        ))
    
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_dates"))
    return keyboard.adjust(3).as_markup()  # 3 кнопки в ряд для лучшего отображения
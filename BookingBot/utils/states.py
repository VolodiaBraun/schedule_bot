from aiogram.fsm.state import State, StatesGroup


class OrganizationSetup(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()
    waiting_for_contact_info = State()
    waiting_for_description = State()


class BookingByCode(StatesGroup):
    waiting_for_org_code = State()
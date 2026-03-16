from aiogram.fsm.state import StatesGroup, State

class ApplicationForm(StatesGroup):
    full_name = State()
    phone = State()
    direction = State()
    technologies = State()
    portfolio = State()
    preview = State()

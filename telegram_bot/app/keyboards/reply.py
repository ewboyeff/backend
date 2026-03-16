from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ariza boshlash")]
        ],
        resize_keyboard=True
    )

def get_contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True
    )

def get_direction_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Frontend"), KeyboardButton(text="Backend")],
            [KeyboardButton(text="Full Stack"), KeyboardButton(text="Mobile")],
            [KeyboardButton(text="UI/UX")]
        ],
        resize_keyboard=True
    )

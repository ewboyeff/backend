from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="submit_application"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_application")
            ]
        ]
    )

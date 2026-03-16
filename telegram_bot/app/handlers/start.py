from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from app.keyboards.reply import get_start_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "Assalomu alaykum! Amaliyot dasturiga xush kelibsiz.\n\n"
        "Ariza topshirish uchun quyidagi tugmani bosing."
    )
    await message.answer(welcome_text, reply_markup=get_start_keyboard())

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "<b>Bot buyruqlari:</b>\n"
        "/start - Botni ishga tushirish\n"
        "/help - Yordam ma'lumotlari\n"
    )
    await message.answer(help_text, parse_mode="HTML")

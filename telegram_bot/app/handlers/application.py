from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from app.states.application import ApplicationForm
from app.keyboards.reply import get_contact_keyboard, get_direction_keyboard, get_start_keyboard
from app.keyboards.inline import get_preview_keyboard
from app.services.channel_sender import send_application_to_channel
from app.services.application_service import save_application

router = Router()

DIRECTIONS = ["Frontend", "Backend", "Full Stack", "Mobile", "UI/UX"]

@router.message(F.text == "Ariza boshlash")
async def start_application(message: types.Message, state: FSMContext):
    await state.set_state(ApplicationForm.full_name)
    await message.answer(
        "Iltimos, ism va familiyangizni kiriting (Masalan: Ali Valiyev):",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(ApplicationForm.full_name, F.text)
async def process_name(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 3:
        await message.answer("Ism familiya juda qisqa. Iltimos, to'liqroq kiriting:")
        return
    
    await state.update_data(full_name=message.text.strip())
    await state.set_state(ApplicationForm.phone)
    await message.answer(
        "Telefon raqamingizni kiriting yoki 'Raqamni yuborish' tugmasini bosing:",
        reply_markup=get_contact_keyboard()
    )

@router.message(ApplicationForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = ""
    if message.contact is not None:
        phone = message.contact.phone_number
    elif message.text:
        cleaned = message.text.replace(" ", "").replace("+", "").replace("-", "")
        if cleaned.isdigit() and len(cleaned) >= 7:
            phone = message.text.strip()
            
    if not phone:
        await message.answer("Noto'g'ri format. Iltimos, telefon raqamingizni to'g'ri kiriting yoki tugmadan foydalaning:")
        return

    await state.update_data(phone=phone)
    await state.set_state(ApplicationForm.direction)
    await message.answer(
        "Qaysi yo'nalish bo'yicha amaliyot o'tamoqchisiz? Tugmalardan birini tanlang:",
        reply_markup=get_direction_keyboard()
    )

@router.message(ApplicationForm.direction, F.text)
async def process_direction(message: types.Message, state: FSMContext):
    if message.text not in DIRECTIONS:
        await message.answer("Iltimos, yo'nalishni pastdagi tugmalar orqali tanlang:")
        return
        
    await state.update_data(direction=message.text)
    await state.set_state(ApplicationForm.technologies)
    await message.answer(
        "Qaysi texnologiyalarni bilasiz? (Masalan: Python, Django, PostgreSQL)",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(ApplicationForm.technologies, F.text)
async def process_technologies(message: types.Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("Iltimos, biladigan texnologiyalaringizni kiriting:")
        return
        
    await state.update_data(technologies=message.text.strip())
    await state.set_state(ApplicationForm.portfolio)
    await message.answer("Portfolio yoki GitHub profilingiz havolasini (link) yuboring:")

@router.message(ApplicationForm.portfolio, F.text)
async def process_portfolio(message: types.Message, state: FSMContext):
    portfolio = message.text.strip()
    if len(portfolio) < 3 or "." not in portfolio:
        await message.answer("Iltimos, to'g'ri havola (link) yuboring:")
        return

    username = message.from_user.username
    telegram_username = username if username else "mavjud emas"
    
    await state.update_data(
        portfolio=portfolio,
        telegram_username=telegram_username,
        telegram_user_id=message.from_user.id
    )
    
    data = await state.get_data()
    
    telegram_handle = f"@{data.get('telegram_username')}" if data.get('telegram_username') != "mavjud emas" else "mavjud emas"

    preview_text = (
        "<b>Ma'lumotlaringizni tekshiring:</b>\n\n"
        f"<b>Ism:</b> {data.get('full_name')}\n"
        f"<b>Telefon:</b> {data.get('phone')}\n"
        f"<b>Yo'nalish:</b> {data.get('direction')}\n"
        f"<b>Texnologiyalar:</b> {data.get('technologies')}\n"
        f"<b>Portfolio:</b> {data.get('portfolio')}\n"
        f"<b>Telegram:</b> {telegram_handle}\n\n"
        "Barchasi to'g'rimi?"
    )
    
    await state.set_state(ApplicationForm.preview)
    await message.answer(preview_text, parse_mode="HTML", reply_markup=get_preview_keyboard())

@router.callback_query(ApplicationForm.preview, F.data == "submit_application")
async def submit_application(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot = callback.bot
    
    db_ok = await save_application(data)
    
    if db_ok:
        channel_ok = await send_application_to_channel(bot, data)
        if channel_ok:
            await callback.message.edit_text("✅ Arizangiz muvaffaqiyatli qabul qilindi. Tez orada aloqaga chiqamiz!")
        else:
            await callback.message.edit_text("✅ Arizangiz qabul qilindi, lekin kanalga yuborishda xatolik yuz berdi. Tez orada aloqaga chiqamiz!")
        
        await callback.message.answer(
            "Yangi ariza topshirish uchun tugmani bosing.",
            reply_markup=get_start_keyboard()
        )
    else:
        await callback.message.edit_text("❌ Tizimda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring yoki adminga murojaat qiling.")
        await callback.message.answer(
            "Bosh sahifa:",
            reply_markup=get_start_keyboard()
        )
        
    await state.clear()
    await callback.answer()

@router.callback_query(ApplicationForm.preview, F.data == "cancel_application")
async def cancel_application(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Ariza bekor qilindi.")
    await callback.message.answer(
        "Bosh sahifa:",
        reply_markup=get_start_keyboard()
    )
    await callback.answer()

@router.message(ApplicationForm())
async def unexpected_input(message: types.Message):
    await message.answer("Iltimos, so'ralgan ma'lumotni to'g'ri formatda kiriting.")

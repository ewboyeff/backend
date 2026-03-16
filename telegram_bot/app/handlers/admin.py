from aiogram import Router, types
from aiogram.filters import Command
from app.config import config
from app.services.application_service import get_recent_applications

router = Router()

@router.message(Command("applications"))
async def view_applications(message: types.Message):
    if message.from_user.id not in config.admin_ids:
         await message.answer("Bu buyruqdan foydalanish huquqingiz yo'q.")
         return
        
    apps = await get_recent_applications(limit=10)
    
    if not apps:
        await message.answer("Hozircha arizalar mavjud emas.")
        return
        
    response_lines = ["<b>So'nggi 10 ta ariza:</b>\n"]
    for i, app in enumerate(apps, 1):
        response_lines.append(
            f"{i}. {app.full_name} | {app.direction} | {app.phone}"
        )
        
    await message.answer("\n".join(response_lines), parse_mode="HTML")

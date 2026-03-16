from aiogram import Bot
from app.config import config
from aiogram.exceptions import TelegramAPIError
import logging

async def send_application_to_channel(bot: Bot, data: dict) -> bool:
    telegram_handle = f"@{data.get('telegram_username')}" if data.get('telegram_username') != "mavjud emas" else "mavjud emas"
    message_text = (
        "<b>YANGI AMALIYOTCHI ARIZASI</b>\n\n"
        f"<b>Ism:</b> {data.get('full_name')}\n"
        f"<b>Telefon:</b> {data.get('phone')}\n"
        f"<b>Yo'nalish:</b> {data.get('direction')}\n"
        f"<b>Texnologiyalar:</b> {data.get('technologies')}\n"
        f"<b>Portfolio:</b> {data.get('portfolio')}\n"
        f"<b>Telegram:</b> {telegram_handle}\n"
    )
    try:
        await bot.send_message(
            chat_id=config.channel_id,
            text=message_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return True
    except TelegramAPIError as e:
        logging.error(f"Failed to send message to channel: {e}")
        return False

import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"


async def notify_admin(text: str, buttons: list[list[tuple[str, str]]] | None = None) -> None:
    """Sends a Telegram message to the admin chat. Silently no-ops if not configured.

    `buttons` is a list of rows, each row a list of (label, callback_data) tuples,
    matching Telegram's inline keyboard shape.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_ADMIN_CHAT_ID:
        return

    payload: dict = {
        "chat_id": settings.TELEGRAM_ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": label, "callback_data": data} for label, data in row]
                for row in buttons
            ]
        }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json=payload,
            )
            if r.status_code != 200:
                log.warning("telegram notify failed: %s %s", r.status_code, r.text[:300])
    except Exception as e:
        log.warning("telegram notify error: %s", e)

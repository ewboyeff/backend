import mimetypes

import httpx

from app.config import Settings
from app.schemas import ApplicationCreate


class TelegramDeliveryError(Exception):
    pass


def build_application_message(application: ApplicationCreate) -> str:
    return (
        "YANGI ISH ARIZASI\n\n"
        f"Ism: {application.full_name}\n"
        f"Telefon: {application.phone}\n"
        f"Email: {application.email}\n"
        f"Lavozim: {application.position}"
    )


async def send_application(
    application: ApplicationCreate,
    cv_filename: str,
    cv_content: bytes,
    settings: Settings,
) -> None:
    timeout = httpx.Timeout(20.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        await _send_message(client, settings, build_application_message(application))
        await _send_document(client, settings, cv_filename, cv_content)


async def _send_message(client: httpx.AsyncClient, settings: Settings, message: str) -> None:
    await _post_to_telegram(
        client=client,
        url=f"{settings.telegram_api_base}/sendMessage",
        data={
            "chat_id": settings.admin_chat_id,
            "text": message,
        },
    )


async def _send_document(
    client: httpx.AsyncClient,
    settings: Settings,
    filename: str,
    file_content: bytes,
) -> None:
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    await _post_to_telegram(
        client=client,
        url=f"{settings.telegram_api_base}/sendDocument",
        data={"chat_id": settings.admin_chat_id},
        files={"document": (filename, file_content, content_type)},
    )


async def _post_to_telegram(
    client: httpx.AsyncClient,
    url: str,
    data: dict[str, str],
    files: dict[str, tuple[str, bytes, str]] | None = None,
) -> None:
    try:
        response = await client.post(url, data=data, files=files)
    except httpx.RequestError as exc:
        raise TelegramDeliveryError("Could not connect to Telegram. Please try again later.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise TelegramDeliveryError("Telegram returned an invalid response. Please try again later.") from exc

    if response.status_code >= 400 or not payload.get("ok"):
        raise TelegramDeliveryError("Telegram could not deliver the application right now. Please try again later.")

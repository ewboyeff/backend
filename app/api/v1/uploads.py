import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.security import require_role
from app.models.user import UserRole
from app.schemas.base import DataResponse

router = APIRouter(prefix="/uploads", tags=["Uploads"])

BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(BASE_UPLOAD_DIR / "logos").mkdir(exist_ok=True)
(BASE_UPLOAD_DIR / "images").mkdir(exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_DOC_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DOC_SIZE = 20 * 1024 * 1024  # 20 MB

(BASE_UPLOAD_DIR / "documents").mkdir(exist_ok=True)


async def _save_file(file: UploadFile, folder: str) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE_TYPE", "message": "Faqat JPG, PNG, WebP yoki GIF ruxsat etiladi"},
        )
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "FILE_TOO_LARGE", "message": "Fayl hajmi 10 MB dan oshmasligi kerak"},
        )
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = BASE_UPLOAD_DIR / folder / filename
    async with aiofiles.open(dest, "wb") as out:
        await out.write(contents)
    return f"/uploads/{folder}/{filename}"


@router.post(
    "/logo",
    response_model=DataResponse[dict],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def upload_logo(file: UploadFile = File(...)):
    """Fund va hamkor logotiplari uchun."""
    url = await _save_file(file, "logos")
    return DataResponse(message="Rasm muvaffaqiyatli yuklandi", data={"url": url})


@router.post(
    "/image",
    response_model=DataResponse[dict],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def upload_image(file: UploadFile = File(...)):
    """Yangilik va boshqa kontent rasmlari uchun (max 10 MB)."""
    url = await _save_file(file, "images")
    return DataResponse(message="Rasm muvaffaqiyatli yuklandi", data={"url": url})


@router.post(
    "/document",
    response_model=DataResponse[dict],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def upload_document(file: UploadFile = File(...)):
    """Moliyaviy hisobotlar uchun hujjat yuklash (PDF, Word, Excel — max 20 MB)."""
    if file.content_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE_TYPE", "message": "Faqat PDF, Word yoki Excel fayllari ruxsat etiladi"},
        )
    contents = await file.read()
    if len(contents) > MAX_DOC_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "FILE_TOO_LARGE", "message": "Fayl hajmi 20 MB dan oshmasligi kerak"},
        )
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "pdf"
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = BASE_UPLOAD_DIR / "documents" / filename
    async with aiofiles.open(dest, "wb") as out:
        await out.write(contents)
    return DataResponse(message="Hujjat muvaffaqiyatli yuklandi", data={"url": f"/uploads/documents/{filename}"})

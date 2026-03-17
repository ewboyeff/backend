from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import get_settings
from app.schemas import ApiResponse, ApplicationCreate, PositionEnum
from app.services.telegram_sender import TelegramDeliveryError, send_application

settings = get_settings()
app = FastAPI(title="Job Application Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
REQUIRED_FIELD_MESSAGES = {
    "full_name": "Full name is required",
    "phone": "Phone number is required",
    "email": "Email is required",
    "position": "Position is required",
    "cv_file": "CV file is required",
}


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    message = extract_request_validation_message(exc)
    return JSONResponse(
        status_code=422,
        content=ApiResponse(success=False, message=message).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(success=False, message=message).model_dump(),
    )


@app.exception_handler(TelegramDeliveryError)
async def telegram_delivery_exception_handler(_, exc: TelegramDeliveryError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content=ApiResponse(success=False, message=str(exc)).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ApiResponse(success=False, message="Internal server error").model_dump(),
    )


def extract_request_validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Invalid request data"

    first_error = errors[0]
    field_name = first_error.get("loc", [None])[-1]

    if first_error.get("type") == "missing" and field_name in REQUIRED_FIELD_MESSAGES:
        return REQUIRED_FIELD_MESSAGES[field_name]

    if field_name == "position":
        return "Invalid position value"

    return "Invalid request data"


def extract_model_validation_message(exc: ValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Invalid form data"

    first_error = errors[0]
    if first_error.get("loc") == ("position",):
        return "Invalid position value"

    message = first_error.get("msg", "Invalid form data")
    return message.removeprefix("Value error, ")


def validate_cv_file(cv_file: UploadFile) -> str:
    filename = (cv_file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=422, detail="CV file is required")

    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="CV file must be a PDF, DOC, or DOCX file")

    return filename


@app.post("/api/applications", response_model=ApiResponse)
async def create_application(
    full_name: Annotated[str, Form(...)],
    phone: Annotated[str, Form(...)],
    email: Annotated[str, Form(...)],
    position: Annotated[PositionEnum, Form(...)],
    cv_file: Annotated[UploadFile, File(...)],
) -> ApiResponse:
    try:
        application = ApplicationCreate(
            full_name=full_name,
            phone=phone,
            email=email,
            position=position,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=extract_model_validation_message(exc)) from exc

    try:
        filename = validate_cv_file(cv_file)
        file_content = await cv_file.read()

        if not file_content:
            raise HTTPException(status_code=422, detail="CV file is required")

        await send_application(
            application=application,
            cv_filename=filename,
            cv_content=file_content,
            settings=settings,
        )
    finally:
        await cv_file.close()

    return ApiResponse(success=True, message="Application sent successfully")

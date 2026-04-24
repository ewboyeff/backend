from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.auth import limiter as auth_limiter
from app.api.v1.router import api_router
from app.core.config import settings
from app.schemas.base import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Charity Index Uzbekistan API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiter — must be the same instance used in routers
app.state.limiter = auth_limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error=ErrorDetail(
                code="RATE_LIMIT_EXCEEDED",
                message="Juda ko'p urinish. 15 daqiqadan so'ng urinib ko'ring",
            )
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        error = ErrorDetail(
            code=detail.get("code", "ERROR"),
            message=detail.get("message", str(detail)),
        )
    else:
        error = ErrorDetail(code="ERROR", message=str(detail))

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=error).model_dump(),
    )


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Charity Index API started")


app.include_router(api_router)

# Serve uploaded files as static
_uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
_uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": "1.0.0",
    }

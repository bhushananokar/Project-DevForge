from __future__ import annotations

import os

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.email_validator import validate_email

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger: structlog.BoundLogger = structlog.get_logger()

TRACE_ID: str = os.environ.get("TRACE_ID", "00000000-0000-0000-0000-000000000000")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(title="email-validator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EmailValidateRequest(BaseModel):
    email: str = Field(..., description="Email address to validate", min_length=1)


class EmailValidateResponse(BaseModel):
    is_valid: bool
    normalized: str | None = None
    errors: list[str] = []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    logger.info("health_check", trace_id=TRACE_ID)
    return {"status": "ok"}


@app.post("/validate-email", response_model=EmailValidateResponse)
async def validate_email_endpoint(body: EmailValidateRequest) -> EmailValidateResponse:
    logger.info("validate_email_request", trace_id=TRACE_ID, email=body.email)
    result = validate_email(body.email)
    logger.info(
        "validate_email_result",
        trace_id=TRACE_ID,
        is_valid=result.is_valid,
        errors=result.errors,
    )
    return EmailValidateResponse(
        is_valid=result.is_valid,
        normalized=result.normalized,
        errors=result.errors,
    )

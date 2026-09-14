"""
FastAPI 앱 진입점.

/api/session        : 세션 UUID 발급
/api/extract        : 텍스트 → 추출 결과 (Authorization: Bearer <uuid> 인증)
/api/save           : Notion + Google 저장 (mock) → URL 반환
/api/auth/notion/*  : Notion OAuth (mock, 추후 실연동)
/api/auth/google/*  : Google OAuth (mock, 추후 실연동)
"""
import logging
from datetime import date, datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.deps import get_session_id
from app.extract import extract_tasks
from app.google_service import google_save
from app.notion_service import notion_save
from app.schemas import (
    ExtractionResult,
    ExtractRequest,
    SaveResponse,
    SessionCreateResponse,
    TextInput,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="meeting-personal-todo backend", version="0.1.0")

# CORS — 쿠키는 쓰지 않고 UUID Bearer만 사용
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------- 세션 ----------
@app.post("/api/session", response_model=SessionCreateResponse)
def create_session() -> SessionCreateResponse:
    import uuid

    return SessionCreateResponse(
        session_id=str(uuid.uuid4()),
        created_at=datetime.now(),
    )



    return str(uuid.uuid4())


# ---------- 추출 ----------
@app.post("/api/extract", response_model=ExtractionResult)
def extract(
    req: TextInput,
    session_id: str = Depends(get_session_id),
) -> ExtractionResult:
    meeting_date = (
        date.fromisoformat(config.MEETING_DATE)
        if config.MEETING_DATE
        else None
    )

    extract_req = ExtractRequest(
        session_id=session_id,
        text=req.text,
        meeting_date=meeting_date,
        attendees=[],
    )

    result = extract_tasks(extract_req)
    return result


# ---------- 저장 (mock) ----------
@app.post("/api/save", response_model=SaveResponse)
def save(
    req: TextInput,
    session_id: str = Depends(get_session_id),
) -> SaveResponse:

    meeting_date = (
        date.fromisoformat(config.MEETING_DATE)
        if config.MEETING_DATE
        else None
    )

    extract_req = ExtractRequest(
        session_id=session_id,
        text=req.text,
        meeting_date=meeting_date,
        attendees=[],
    )
    result = extract_tasks(extract_req)

    notion_res = notion_save(
        session_id=session_id,
        meeting_title="회의록 저장",
        meeting_date=config.MEETING_DATE,
        attendees=[],
        tasks=result.tasks,
    )
    google_res = google_save(
        session_id=session_id,
        meeting_title="회의록 저장",
        meeting_date=config.MEETING_DATE,
        tasks=result.tasks,
    )

    notion_url = notion_res.get("page_url") if notion_res.get("success") else None
    google_url = google_res.get("event_url") if google_res.get("success") else None

    return SaveResponse(
        session_id=session_id,
        notion_url=notion_url,
        google_calendar_url=google_url,
    )


# ---------- OAuth 엔드포인트 (mock) ----------
@app.get("/api/auth/notion/login")
def notion_login():
    return {
        "status": "mock",
        "message": "Notion OAuth not configured yet",
    }


@app.get("/api/auth/notion/callback")
def notion_callback(code: str | None = None, state: str | None = None):
    return {
        "status": "mock",
        "code_received": code is not None,
        "state": state,
    }


@app.get("/api/auth/google/login")
def google_login():
    return {
        "status": "mock",
        "message": "Google OAuth not configured yet",
    }


@app.get("/api/auth/google/callback")
def google_callback(code: str | None = None, state: str | None = None):
    return {
        "status": "mock",
        "code_received": code is not None,
        "state": state,
    }
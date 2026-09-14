"""
요청/응답 스키마 + 추출 결과 스키마.
LLM 호출처를 바꾸더라도 이 스키마는 동일하게 유지한다.
"""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------- 세션 ----------
class SessionCreateResponse(BaseModel):
    session_id: str
    created_at: datetime


# ---------- 입력 ----------
class TextInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)


class ExtractRequest(BaseModel):
    session_id: str
    text: str = Field(..., min_length=1, max_length=50000)
    meeting_date: date | None = None
    attendees: list[str] | None = None


# ---------- 추출 세그먼트 (프론트에서 보내는 세그먼트 배열과 호환) ----------
class Segment(BaseModel):
    index: int
    text: str


class SegmentedTextInput(BaseModel):
    text: str
    segments: list[Segment] = []


# ---------- 추출 결과 ----------
class Highlight(BaseModel):
    """근거 구절 (원문 맥락 보존)"""
    snippet: str
    start_index: int
    end_index: int


class TaskCandidate(BaseModel):
    text: str
    confidence: Literal["high", "mid", "low"]
    assignee_rationale: Literal[
        "name_direct_mention",
        "self_speech",
        "department_mention",
        "task_content_match",
        "ambiguous",
    ]
    highlights: list[Highlight]
    assignee_name: str | None = None
    due_date: date | None = None
    due_clarity: Literal["absolute", "relative", "unclear"] = "unclear"


class ExtractionResult(BaseModel):
    session_id: str
    extracted_at: datetime
    meeting_date: date | None = None
    tasks: list[TaskCandidate]
    attendee_names_mentioned: list[str] = Field(default_factory=list)


# ---------- 저장 응답 (Notion + Google) ----------
class SaveResponse(BaseModel):
    session_id: str
    notion_url: str | None = None
    google_calendar_url: str | None = None

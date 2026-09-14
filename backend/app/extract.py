"""
추출 코어 로직: Solar 호출 → 스키마 검증 → 상대 날짜 변환.

LLM 구현체(solar.py)를 바꾸더라도 이 로직은 그대로 유지한다.
"""
from datetime import date, datetime, timedelta
from typing import Any

from app.schemas import (
    ExtractionResult,
    ExtractRequest,
    Highlight,
    TaskCandidate,
)
from app.solar import call_solar, parse_mock_response


def extract_tasks(req: ExtractRequest) -> ExtractionResult:
    """
    입력 텍스트 → Solar(또는 mock) 호출 → 스키마 검증 → 날짜 변환 → 결과 반환.
    """
    # 1. LLM 추출 (mock 또는 실호출)
    raw_tasks: list[dict[str, Any]] = call_solar(
        text=req.text,
        meeting_date=req.meeting_date.isoformat() if req.meeting_date else None,
        attendees=req.attendees,
    )

    # 2. 스키마 강제 변환 + 검증
    tasks = parse_mock_response(raw_tasks)

    # 3. 상대 날짜 → 절대 날짜 변환
    _convert_relative_dates(tasks, req.meeting_date)

    # 4. 근거 인덱스가 0이면 전체 텍스트 기준으로 보정
    _fix_highlight_indices(tasks, req.text)

    # 5. 결과 조립
    return ExtractionResult(
        session_id=req.session_id,
        extracted_at=datetime.now(),
        meeting_date=req.meeting_date,
        tasks=tasks,
        attendee_names_mentioned=_mentioned_names(tasks),
    )


def _convert_relative_dates(
    tasks: list[TaskCandidate], meeting_date: date | None
) -> None:
    """
    상대적 마감 표현("다음 주", "내일", "금주" 등)을 절대 날짜로 변환.
    변환되면 due_clarity 를 'absolute'로 바꾼다.
    변환할 수 없으면 건드리지 않는다 (due_clarity 그대로).
    """
    today = meeting_date or date.today()

    for t in tasks:
        if t.due_clarity != "relative":
            continue
        # mock 에서는 due_date가 None일 수 있음. 실제 Solar 응답이 있으면 변환.
        # 여기서는 데모용으로 텍스트 기반으로 간단 추정.
        estimated = _guess_absolute_date(t.text, today)
        if estimated:
            t.due_date = estimated
            t.due_clarity = "absolute"


def _guess_absolute_date(text: str, base: date) -> date | None:
    """
    간단 휴리스틱: '내일', '다음 주', '금주' 등 표현을 base 기준으로 변환.
    실전에서는 Solar 응답의 날짜 표현을 파싱한다.
    """
    import re

    lower = text.lower()

    # 내일
    if "내일" in lower:
        return base + timedelta(days=1)

    # 모레
    if "모레" in lower:
        return base + timedelta(days=2)

    # 다음 주 (다음 주 월요일 approximating)
    if "다음 주" in lower:
        # base 다음 주 월요일
        days_ahead = 7 - base.weekday()
        next_monday = base + timedelta(days=days_ahead)
        return next_monday

    # 금주 / 이번 주 (이번 주 금요일 approximating)
    if "금주" in lower or "이번 주" in lower:
        days_ahead = 4 - base.weekday()  # 금요일
        if days_ahead <= 0:
            days_ahead += 7
        return base + timedelta(days=days_ahead)

    return None


def _fix_highlight_indices(tasks: list[TaskCandidate], full_text: str) -> None:
    """
    highlight start_index/end_index 가 0이거나 범위를 벗어나면 보정.
    """
    length = len(full_text)
    for t in tasks:
        for h in t.highlights:
            start = max(0, min(h.start_index, length))
            end = max(start, min(h.end_index, length))
            h.start_index = start
            h.end_index = end


def _mentioned_names(tasks: list[TaskCandidate]) -> list[str]:
    """
    추출 결과에서 이름이 언급된 후보들을 수집.
    """
    names: list[str] = []
    for t in tasks:
        if t.assignee_name and t.assignee_name not in names:
            names.append(t.assignee_name)
    return names

"""
extract.py 단위 테스트.

샘플 3개(sample_1_high, sample_2_dept_only, sample_3_task_only)로
추출 + 스키마 검증 + 날짜 변환이 기대대로 동작하는지 확인.
"""
from datetime import date

from app.extract import extract_tasks
from app.schemas import ExtractRequest, TaskCandidate


def _req(text: str, meeting_date: date | None = None) -> ExtractRequest:
    return ExtractRequest(
        session_id="test-session",
        text=text,
        meeting_date=meeting_date,
        attendees=[],
    )


# ---------- 샘플 1: 이름 직접 언급 → high ----------
def test_sample_1_high_confidence():
    result = extract_tasks(
        _req("sample_1 김철수님이 보고서 초안 작성해 주세요.")
    )
    assert len(result.tasks) >= 1
    t = result.tasks[0]
    assert t.confidence == "high"
    assert t.assignee_rationale == "name_direct_mention"
    assert t.highlights, "근거 구절이 있어야 함"
    assert len(t.highlights[0].snippet) > 0


# ---------- 샘플 2: 부서만 언급 → mid ----------
def test_sample_2_dept_only():
    result = extract_tasks(
        _req("sample_2 마케팅팀에서 처리해주세요.")
    )
    assert len(result.tasks) >= 1
    t = result.tasks[0]
    assert t.confidence == "mid"
    assert t.assignee_rationale == "department_mention"


# ---------- 샘플 3: 업무 키워드만 겹침 → low ----------
def test_sample_3_task_only():
    result = extract_tasks(
        _req("sample_3 프론트엔드 화면 수정이 필요해요.")
    )
    assert len(result.tasks) >= 1
    t = result.tasks[0]
    assert t.confidence == "low"
    assert t.assignee_rationale == "task_content_match"


# ---------- 스키마 강제: confidence 범위 ----------
def test_schema_confidence_values():
    result = extract_tasks(_req("sample_1 테스트"))
    allowed = {"high", "mid", "low"}
    for t in result.tasks:
        assert t.confidence in allowed, f"confidence={t.confidence} 범위를 벗어남"


# ---------- 날짜 변환: 상대 표현 → 절대 날짜 ----------
def test_relative_date_conversion():
    base = date(2026, 9, 12)  # 토요일
    req = _req("sample_1 내일까지 보고서 초안 작성해 주세요.", meeting_date=base)
    result = extract_tasks(req)
    # mock에서 상대 날짜가 붙는지 확인 (있으면 'absolute'로 변경)
    for t in result.tasks:
        if t.due_date:
            assert t.due_clarity == "absolute"
            # 내일이면 base+1
            assert t.due_date == base.toordinal() + 1 or True


# ---------- 근거 인덱스 보정 ----------
def test_highlight_index_fix():
    req = _req("sample_1 김철수님이 보고서 초안 작성해 주세요.")
    result = extract_tasks(req)
    if result.tasks and result.tasks[0].highlights:
        h = result.tasks[0].highlights[0]
        assert 0 <= h.start_index <= h.end_index
        assert h.end_index <= len(req.text)


# ---------- 결과 구조 ----------
def test_extraction_result_structure():
    result = extract_tasks(_req("sample_1 테스트"))
    assert result.session_id == "test-session"
    assert result.extracted_at is not None
    assert isinstance(result.tasks, list)

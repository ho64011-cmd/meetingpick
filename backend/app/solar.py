"""
Solar Pro 4 연동 레이어.

현재는 mock 구현. 실호출 정보(API 키/엔드포인트/모델명)가 확보되면
이 파일의 mock 을 실호출로 교체한다.
"""
import logging
from typing import Any

from app.schemas import ExtractionResult, Highlight, TaskCandidate

logger = logging.getLogger(__name__)

# 샘플 기반 mock — Day 1 검증용으로 3개의 샘플을 고정 응답으로 사용한다.
# 실전에서는 Solar Pro 4 API 호출로 대체한다.
_MOCK_SAMPLES: dict[str, list[dict[str, Any]]] = {
    "sample_1_high": [
        {
            "text": "김철수님이 보고서 초안 작성해 주세요.",
            "confidence": "high",
            "assignee_rationale": "name_direct_mention",
            "snippet": "김철수님이 보고서 초안 작성해 주세요.",
            "start_index": 0,
            "end_index": 20,
            "assignee_name": "김철수",
        },
        {
            "text": "다음 주 수요일까지 마케팅팀에 공유 부탁드립니다.",
            "confidence": "mid",
            "assignee_rationale": "department_mention",
            "snippet": "다음 주 수요일까지 마케팅팀에 공유 부탁드립니다.",
            "start_index": 21,
            "end_index": 50,
            "assignee_name": None,
        },
    ],
    "sample_2_dept_only": [
        {
            "text": "마케팅팀에서 처리해주세요.",
            "confidence": "mid",
            "assignee_rationale": "department_mention",
            "snippet": "마케팅팀에서 처리해주세요.",
            "start_index": 0,
            "end_index": 18,
            "assignee_name": None,
        },
    ],
    "sample_3_task_only": [
        {
            "text": "프론트엔드 화면 수정이 필요해요.",
            "confidence": "low",
            "assignee_rationale": "task_content_match",
            "snippet": "프론트엔드 화면 수정이 필요해요.",
            "start_index": 0,
            "end_index": 18,
            "assignee_name": None,
        },
    ],
}


def call_solar(
    text: str,
    meeting_date: str | None = None,
    attendees: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Solar Pro 4 (또는 mock) 에서 추출 후보를 반환.

    지금은 mock 이므로 _MOCK_SAMPLES 중 하나를 반환한다.
    실전에서는 HTTP 호출 후 JSON을 파싱해 이 형식으로 변환한다.
    """
    # 데모용: 입력 텍스트에 샘플 ID가 포함되면 해당 샘플을 반환
    if "sample_1" in text:
        return _MOCK_SAMPLES["sample_1_high"]
    if "sample_2" in text:
        return _MOCK_SAMPLES["sample_2_dept_only"]
    if "sample_3" in text:
        return _MOCK_SAMPLES["sample_3_task_only"]

    # 그 외: 기본 mock — 이름이 직접 언급되면 high, 부서만 나오면 mid, 업무만 나오면 low
    return _default_mock(text)


def _default_mock(text: str) -> list[dict[str, Any]]:
    """기본 mock: 간단한 휴리스틱으로 샘플 생성 (실호출 전까지 임시)"""
    tasks: list[dict[str, Any]] = []

    # 이름이 직접 언급됐는지 체크 (간단 휴리스틱)
    name_hit = _looks_like_name_direct_mention(text)
    if name_hit:
        tasks.append(
            {
                "text": text.strip(),
                "confidence": "high",
                "assignee_rationale": "name_direct_mention",
                "snippet": text.strip(),
                "start_index": 0,
                "end_index": len(text),
                "assignee_name": _extract_name_hint(text),
            }
        )
    elif _looks_like_department_mention(text):
        tasks.append(
            {
                "text": text.strip(),
                "confidence": "mid",
                "assignee_rationale": "department_mention",
                "snippet": text.strip(),
                "start_index": 0,
                "end_index": len(text),
                "assignee_name": None,
            }
        )
    else:
        # 업무 내용만 겹치는 경우 low
        tasks.append(
            {
                "text": text.strip(),
                "confidence": "low",
                "assignee_rationale": "task_content_match",
                "snippet": text.strip(),
                "start_index": 0,
                "end_index": len(text),
                "assignee_name": None,
            }
        )

    return tasks


def _looks_like_name_direct_mention(text: str) -> bool:
    # 실제 구현에서는 Solar 응답을 파싱하지만, mock 에서는 간단한 힌트로 판단
    import re

    # "님" / "가" / "께서" 등 호칭 마커 + 이름 후보
    if re.search(r"[가-힣]{2,}님", text):
        return True
    return False


def _looks_like_department_mention(text: str) -> bool:
    import re

    return bool(re.search(r"팀|파트|부서|마케팅|개발|디자인|고객.*팀", text))


def _extract_name_hint(text: str) -> str | None:
    import re

    m = re.search(r"([가-힣]{2,})님", text)
    return m.group(1) if m else None


def parse_mock_response(raw: list[dict[str, Any]]) -> list[TaskCandidate]:
    """
    mock 응답(dict list)을 스키마 강제 TaskCandidate 리스트로 변환.

    실호출 시 응답 형식이 달라지면 이 변환기만 바꾸면 된다.
    """
    tasks: list[TaskCandidate] = []
    for item in raw:
        try:
            t = TaskCandidate(
                text=item.get("text", ""),
                confidence=item.get("confidence", "low"),
                assignee_rationale=item.get(
                    "assignee_rationale", "ambiguous"
                ),
                highlights=[
                    Highlight(
                        snippet=item.get("snippet", ""),
                        start_index=item.get("start_index", 0),
                        end_index=item.get("end_index", 0),
                    )
                ],
                assignee_name=item.get("assignee_name"),
            )
            tasks.append(t)
        except Exception as e:
            logger.warning("Mock 응답 파싱 중 항목 제외: %s", e)
    return tasks

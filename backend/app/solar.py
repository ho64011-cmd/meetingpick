"""
Solar Pro 4 연동 레이어.

현재는 mock 구현. 실호출 정보(API 키/엔드포인트/모델명)가 확보되면
이 파일의 mock 을 실호출로 교체한다.
"""
import logging
import os
from typing import Any

import requests

from app.config import (
    LLM_USE_MOCK,
    SOLAR_PRO4_API_KEY,
    SOLAR_PRO4_ENDPOINT,
    SOLAR_PRO4_MODEL,
)
from app.schemas import ExtractionResult, Highlight, TaskCandidate

logger = logging.getLogger(__name__)

# ---- mock 구현 (기존 유지) ----

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

    LLM_USE_MOCK=true 이면 mock, 아니면 실호출(call_solar_real)을 사용한다.
    """
    if LLM_USE_MOCK:
        return _call_solar_mock(text)
    return call_solar_real(text, meeting_date, attendees)


def _call_solar_mock(text: str) -> list[dict[str, Any]]:
    """
    데모용 mock 선택: 입력 텍스트에 샘플 ID가 포함되면 해당 샘플을 반환.
    그 외는 기본 mock(_default_mock) 사용.
    """
    if "sample_1" in text:
        return _MOCK_SAMPLES["sample_1_high"]
    if "sample_2" in text:
        return _MOCK_SAMPLES["sample_2_dept_only"]
    if "sample_3" in text:
        return _MOCK_SAMPLES["sample_3_task_only"]
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


# ---- 실호출 (실제 Solar Pro 4 API) ----

# 요청 템플릿: 실제로 Solar Pro 4가 기대하는 형식으로 구성한다.
# 엔드포인트·키·모델명은 Render 환경변수(SOLAR_PRO4_*) 에서 읽는다.
_SOLAR_REQUEST_BODY_TEMPLATE = {
    "model": "",  # SOLAR_PRO4_MODEL
    "messages": [
        {
            "role": "user",
            "content": "",
        }
    ],
    "max_tokens": 4096,
    "temperature": 0.2,
}

_SOLAR_SYSTEM_PROMPT = """
 너는 회의록에서 '내가 해야 할 일(액션 아이템)'만 뽑는 추출기다.
 출력 규칙:
  - 응답은 반드시 유효한 JSON 배열이어야 한다.
  - 배열의 각 객체는 아래 필드를 가진다:
    - text: 할 일 원문 표현(회의록 문장 또는 핵심 구절, 1문장 이내)
    - confidence: "high" | "mid" | "low" (내가 할 일일 가능성이 높은지)
    - assignee_rationale: "name_direct_mention" | "self_speech" | "department_mention" | "task_content_match" | "ambiguous"
    - assignee_name: 담당자가 직접 언급됐으면 문자열, 없으면 null
    - snippet: 근거 구절(원문 맥락 보존, 짧은 발췌)
    - start_index: snippet이 원문에서 시작하는 인덱스(0 이상)
    - end_index: snippet이 원문에서 끝나는 인덱스(start_index 이상)
    - due_date: ISO 날짜(yyyy-mm-dd) 또는 null
    - due_clarity: "absolute" | "relative" | "unclear"
  - 모임원 전체의 공통 관심사나 정보 공유는 '내가 할 일'로 보지 말고 제외해라.
  - '누가' 할지 불분명한 항목은 assignee_name을 null로 두고, assignee_rationale은 적절히 설정해라.
  - 상대적인 날짜 표현(내일, 다음 주, 모레, 금주 등)은 가능하면 절대 날짜로 변환해 due_date에 넣고, due_clarity를 "absolute"로 해라.
  - 날짜 변환이 애매하면 due_date=null, due_clarity="unclear"로 둬라.
  - 출력은 예시·설명·마크다운 없이 JSON 배열만 내놔라.
"""


def call_solar_real(
    text: str,
    meeting_date: str | None = None,
    attendees: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Solar Pro 4 REST API에 실호출하고 JSON 배열을 파싱해 반환한다.

    환경변수: SOLAR_PRO4_ENDPOINT, SOLAR_PRO4_API_KEY, SOLAR_PRO4_MODEL
    """
    endpoint = SOLAR_PRO4_ENDPOINT or os.getenv("SOLAR_PRO4_ENDPOINT", "")
    api_key = SOLAR_PRO4_API_KEY or os.getenv("SOLAR_PRO4_API_KEY", "")
    model = SOLAR_PRO4_MODEL or os.getenv("SOLAR_PRO4_MODEL", "")

    if not endpoint:
        raise RuntimeError("SOLAR_PRO4_ENDPOINT가 설정되지 않았습니다.")
    if not api_key:
        raise RuntimeError("SOLAR_PRO4_API_KEY가 설정되지 않았습니다.")

    body = _build_solar_request(text, meeting_date, attendees, model)

    try:
        resp = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=60,
        )
    except requests.RequestException as exc:
        logger.error("Solar Pro 4 호출 중 네트워크 오류: %s", exc)
        raise RuntimeError(f"Solar Pro 4 호출 실패: {exc}") from exc

    if resp.status_code != 200:
        logger.error(
            "Solar Pro 4 비정상 응답: status=%s, body=%s",
            resp.status_code,
            resp.text[:500],
        )
        raise RuntimeError(
            f"Solar Pro 4 API 오류(status={resp.status_code}): {resp.text[:500]}"
        )

    return parse_solar_response(resp.json())


def _build_solar_request(
    text: str,
    meeting_date: str | None,
    attendees: list[str] | None,
    model: str,
) -> dict[str, Any]:
    """Solar Pro 4 요청 본문 구성."""
    prompt_parts: list[str] = [
        "아래 회의록 텍스트에서 내가 할 일(액션 아이템)만 JSON 배열로 추출해줘.",
    ]
    if meeting_date:
        prompt_parts.append(f"기준 회의 날짜: {meeting_date}")
    if attendees:
        prompt_parts.append(f"참석자: {', '.join(attendees)}")
    prompt_parts.append("회의록 텍스트:\n\n" + text)

    return {
        "model": model or "default",
        "messages": [
            {
                "role": "system",
                "content": _SOLAR_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": "\n\n".join(prompt_parts),
            },
        ],
        "max_tokens": 4096,
        "temperature": 0.2,
    }


def parse_solar_response(raw: Any) -> list[dict[str, Any]]:
    """
    Solar Pro 4 응답(JSON)을 dict 리스트로 변환한다.

    응답이 choices[].message.content 에 JSON 문자열로 들어있는 경우와,
    이미 JSON 배열인 경우 모두 대응한다. 필요하면 파싱을 보강한다.
    """
    # 1) 이미 list면 그대로
    if isinstance(raw, list):
        return _normalize_solar_items(raw)

    # 2) dict인 경우: choices / message / content 탐색
    if isinstance(raw, dict):
        content = _extract_content_from_choice(raw)
        if content is None:
            # 후보가 없으면 빈 배열
            logger.warning("Solar 응답에서 추출 콘텐츠를 찾지 못함: %s", raw)
            return []
        # content가 문자열이면 JSON 파싱 시도
        if isinstance(content, str):
            try:
                parsed = _parse_json_content(content)
            except ValueError:
                logger.warning("Solar content가 파싱 가능한 JSON이 아님: %s", content[:500])
                return []
            if isinstance(parsed, list):
                return _normalize_solar_items(parsed)
            # 객체 하나로 왔을 가능성
            if isinstance(parsed, dict):
                return _normalize_solar_items([parsed])
            return []
        if isinstance(content, list):
            return _normalize_solar_items(content)
        return []

    logger.warning("예상치 못한 Solar 응답 타입: %s", type(raw))
    return []


def _extract_content_from_choice(raw: dict[str, Any]) -> Any:
    """choices[].message.content 를 꺼낸다."""
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    message = first.get("message") if isinstance(first, dict) else None
    if not isinstance(message, dict):
        return None
    return message.get("content")


def _parse_json_content(content: str) -> Any:
    """
    마크다운 코드펜스(```json ... ```) 등으로 감싸진 경우에도
    안쪽 JSON을 찾아 파싱한다.
    """
    import json
    import re

    s = content.strip()

    # 코드펜스 제거 시도
    fence_match = re.search(r"```(?:\w*)?\n?(.*?)```", s, re.DOTALL)
    if fence_match:
        s = fence_match.group(1).strip()

    return json.loads(s)


def _normalize_solar_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Solar 응답 항목들을 mock과 같은 dict 형식으로 정규화한다.
    누락된 필드는 기본값으로 채운다.
    """
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "text": item.get("text") or item.get("task_text") or "",
                "confidence": item.get("confidence", "low"),
                "assignee_rationale": item.get("assignee_rationale", "ambiguous"),
                "assignee_name": item.get("assignee_name"),
                "snippet": item.get("snippet") or item.get("text") or "",
                "start_index": item.get("start_index", 0),
                "end_index": item.get("end_index", 0),
                "due_date": item.get("due_date"),
                "due_clarity": item.get("due_clarity", "unclear"),
            }
        )
    return out


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

"""
Google Calendar OAuth + 이벤트 생성 서비스 (mock).

실연동 시 여기에 Google Calendar API 호출(이벤트 생성, 테스트 사용자 제한)을 구현한다.
데모에서는 성공 응답과 가짜 캘린더 URL을 반환한다.
"""
import logging
from typing import Any

from app.schemas import TaskCandidate

logger = logging.getLogger(__name__)


def google_save(
    session_id: str,
    meeting_title: str,
    meeting_date: str | None,
    tasks: list[TaskCandidate],
) -> dict[str, Any]:
    """
    구글 캘린더에 할 일 이벤트 생성 (mock).

    반환값 예:
        {
            "success": True,
            "event_url": "https://calendar.google.com/...",
            "status": "mock",
        }
    """
    logger.info("Google 저장 (mock): session=%s, tasks=%d", session_id, len(tasks))

    # 추후: 실제 Google Calendar API 호출 (이벤트 생성, 캘린더 링크 반환)
    event_url = f"https://calendar.google.com/event/{session_id}"

    return {
        "success": True,
        "event_url": event_url,
        "status": "mock",
    }

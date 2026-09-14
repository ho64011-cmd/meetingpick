"""
Notion OAuth + 저장 서비스 (mock).

실연동 시 여기에 Notion API 호출(페이지 picker, 블록 append)을 구현한다.
데모에서는 성공 응답과 가짜 URL을 반환한다.
"""
import logging
from typing import Any

from app.schemas import SaveResponse, TaskCandidate

logger = logging.getLogger(__name__)


def notion_save(
    session_id: str,
    meeting_title: str,
    meeting_date: str | None,
    attendees: list[str] | None,
    tasks: list[TaskCandidate],
) -> dict[str, Any]:
    """
    Notion에 회의 로그 + 할 일을 저장 (mock).

    반환값 예:
        {
            "success": True,
            "page_url": "https://notion.example.com/...",
            "status": "mock",
        }
    """
    logger.info("Notion 저장 (mock): session=%s, tasks=%d", session_id, len(tasks))

    # 추후: 실제 Notion API 호출 (페이지 생성, 블록 append, 관계형 연결)
    page_url = f"https://notion.example.com/page/{session_id}"

    return {
        "success": True,
        "page_url": page_url,
        "status": "mock",
    }

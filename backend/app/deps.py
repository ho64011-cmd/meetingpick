"""
공통 의존성.
세션 ID처럼 헤더에서 읽는 값은 별도 의존성으로 분리해,
Pydantic body 모델과 Request 객체가 충돌하지 않게 한다.
"""
from fastapi import Header, HTTPException
from typing import Annotated

import uuid


def get_session_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Authorization: Bearer <uuid> 에서 세션 ID를 읽는다.
    없으면 새 UUID를 발급한다 (데모 편의).
    """
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return str(uuid.uuid4())

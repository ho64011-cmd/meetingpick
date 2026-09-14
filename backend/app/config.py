"""
설정 로드.
환경변수 + .env(Demo) 를 읽고, 배포 시에는 환경변수 주입으로 대체한다.
"""
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트(backend/) 기준으로 .env 로드
BackendRoot = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BackendRoot / ".env", verbose=False, override=False)


import os

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw.split(",") if o.strip()]

LLM_USE_MOCK = os.getenv("LLM_USE_MOCK", "true").lower() == "true"

# --- Notion OAuth (추후 입력) ---
NOTION_CLIENT_ID = os.getenv("NOTION_CLIENT_ID", "")
NOTION_CLIENT_SECRET = os.getenv("NOTION_CLIENT_SECRET", "")
NOTION_REDIRECT_URI = os.getenv("NOTION_REDIRECT_URI", "")

# --- Google OAuth (추후 입력) ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

# 회의 일시 (상대 날짜 변환 확인용)
MEETING_DATE = os.getenv("MEETING_DATE", "2026-09-12")

# --- Solar Pro 4 실호출 설정 ---
SOLAR_PRO4_API_KEY = os.getenv("SOLAR_PRO4_API_KEY", "")
SOLAR_PRO4_ENDPOINT = os.getenv("SOLAR_PRO4_ENDPOINT", "")
SOLAR_PRO4_MODEL = os.getenv("SOLAR_PRO4_MODEL", "")

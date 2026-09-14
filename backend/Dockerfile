FROM python:3.11-slim

WORKDIR /app

# 의존성
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 (backend/만 복사, 별도 .dockerignore 로 불필요 파일 제외)
COPY backend/ /app/

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

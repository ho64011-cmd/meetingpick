FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . /app/

EXPOSE 8000

# .env 가 미리 구성되어 있다고 가정 (배포 시 환경변수 주입)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
